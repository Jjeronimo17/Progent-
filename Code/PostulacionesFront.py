import streamlit as st

from documentos import consultarCarta, guardarCarta
from formularios import consultarRespuestas, generarRespuestas, guardarRespuestas, leerFormulario
from postulaciones import consultarPostulaciones

# En la base los estados van sin tilde, como los demás ENUM del modelo.
ETIQUETAS_ESTADO = {"En revision": "En revisión"}


def etiqueta_estado(estado):
    return ETIQUETAS_ESTADO.get(estado, estado)


def mostrar_informacion_vacante(postulacion):
    with st.expander("Ver información de la vacante"):
        if postulacion["Estado_vacante"] == "Cerrada":
            st.warning("Esta vacante ya fue cerrada y no recibe más postulaciones.")
        st.markdown("**Descripción**")
        st.write(postulacion["Descripcion"])
        st.markdown("**Requisitos**")
        st.write(postulacion["Requisitos"])
        st.caption(f"Publicada el {postulacion['Fecha_publicacion']:%d/%m/%Y}")


def seccion_carta(id_postulacion):
    """Adjuntar, ver, descargar o reemplazar la carta de presentación de una postulación."""
    correo = st.session_state["usuario_logueado"]
    mensaje = st.session_state.pop(f"mensaje_carta_{id_postulacion}", None)
    if mensaje:
        exito, texto = mensaje
        (st.success if exito else st.error)(texto)

    exito, carta = consultarCarta(correo, id_postulacion)
    if not exito:
        st.error(carta)
        return
    if carta:
        st.write(f"Carta adjunta: **{carta['Nombre_archivo']}**")
        st.caption(f"Cargada el {carta['Fecha_carga']:%d/%m/%Y %H:%M}")
        st.download_button(
            "Descargar carta",
            data=bytes(carta["Archivo_bytes"]),
            file_name=carta["Nombre_archivo"],
            mime=carta["Tipo"],
            key=f"descargar_carta_{id_postulacion}",
        )

    # El contador cambia la key del cargador para vaciarlo después de guardar.
    numero = st.session_state.get(f"cargas_carta_{id_postulacion}", 0)
    archivo = st.file_uploader(
        ("Reemplazar la carta" if carta else "Adjuntar carta de presentación")
        + " (PDF o Word, máx. 2 MB)",
        key=f"carta_{id_postulacion}_{numero}",
    )
    if st.button("Guardar carta", key=f"guardar_carta_{id_postulacion}", disabled=archivo is None):
        exito, texto = guardarCarta(correo, id_postulacion, archivo.name, archivo.getvalue())
        st.session_state[f"mensaje_carta_{id_postulacion}"] = (exito, texto)
        if exito:
            st.session_state[f"cargas_carta_{id_postulacion}"] = numero + 1
        st.rerun()


def mostrar_campo_propuesto(id_postulacion, i, campo, numero):
    """Una respuesta propuesta: aviso según su estado, texto editable y opción de rechazarla."""
    st.markdown(f"**{i + 1}. {campo['pregunta']}**")
    if campo["estado"] == "personal":
        st.caption("Dato tomado de tu perfil. No se envió al agente.")
    elif campo["estado"] == "dudoso":
        st.warning(f"No estoy seguro de esta respuesta: {campo['nota'] or 'revísala'}. Revísala antes de confirmar.")
    elif campo["estado"] == "manual":
        st.error(f"No sé cómo llenar este campo: {campo['nota']} Complétalo tú.")
    texto = st.text_area(
        "Respuesta", value=campo["respuesta"], key=f"resp_{id_postulacion}_{numero}_{i}",
        label_visibility="collapsed",
    )
    rechazada = st.checkbox("Rechazar esta respuesta", key=f"rechazar_{id_postulacion}_{numero}_{i}")
    return texto.strip(), rechazada


def seccion_formulario(id_postulacion):
    """Pegar o subir el formulario, revisar lo que propone el agente y confirmar."""
    correo = st.session_state["usuario_logueado"]
    clave = f"formulario_{id_postulacion}"
    mensaje = st.session_state.pop(f"mensaje_{clave}", None)
    if mensaje:
        exito, texto = mensaje
        (st.success if exito else st.error)(texto)

    exito, guardadas = consultarRespuestas(correo, id_postulacion)
    if not exito:
        st.error(guardadas)
    elif guardadas:
        st.markdown("**Respuestas confirmadas** — cópialas en el portal de la empresa. Progent no envía el formulario.")
        for r in guardadas:
            st.markdown(f"*{r['Pregunta']}*")
            st.code(r["Respuesta"], language=None)

    propuesta = st.session_state.get(clave)
    if propuesta is None:
        texto = st.text_area("Pega aquí el formulario de la vacante", key=f"texto_{clave}", height=120)
        archivo = st.file_uploader("…o súbelo (PDF o Word)", key=f"archivo_{clave}")
        if st.button("Llenar con el agente", key=f"procesar_{clave}"):
            if archivo is not None and not texto.strip():
                leido, texto = leerFormulario(archivo.name, archivo.getvalue())
                if not leido:
                    st.error(texto)
                    return
            with st.spinner("El agente está leyendo el formulario..."):
                exito, resultado = generarRespuestas(correo, id_postulacion, texto)
            if not exito:
                st.error(resultado)
            elif resultado["errores"]:
                st.error(" ".join(resultado["errores"]))
            else:
                st.session_state[clave] = resultado["campos"]
                st.session_state[f"numero_{clave}"] = st.session_state.get(f"numero_{clave}", 0) + 1
                st.rerun()
        return

    numero = st.session_state.get(f"numero_{clave}", 0)
    st.caption("Respuestas propuestas por el agente. Edítalas, rechaza las que no sirvan y confirma.")
    with st.form(f"form_{clave}_{numero}"):
        resultados = [mostrar_campo_propuesto(id_postulacion, i, c, numero) for i, c in enumerate(propuesta)]
        confirmar = st.form_submit_button("Confirmar respuestas", type="primary")
    if st.button("Descartar propuesta", key=f"descartar_{clave}"):
        st.session_state.pop(clave, None)
        st.rerun()

    if confirmar:
        aceptadas = [(c["pregunta"], t) for c, (t, rechazada) in zip(propuesta, resultados) if not rechazada]
        vacias = [p for p, t in aceptadas if not t]
        if vacias:
            st.error("Completa o rechaza estas preguntas antes de confirmar: " + "; ".join(vacias))
            return
        if not aceptadas:
            st.error("Rechazaste todas las respuestas; no hay nada que guardar.")
            return
        exito, texto = guardarRespuestas(correo, id_postulacion, aceptadas)
        st.session_state[f"mensaje_{clave}"] = (exito, texto)
        if exito:
            st.session_state.pop(clave, None)
        st.rerun()


def mostrar_panel_postulaciones():
    st.title("Mis postulaciones")

    exito, resultado = consultarPostulaciones(st.session_state["usuario_logueado"])

    if not exito:
        st.error(resultado)
        return

    if not resultado:
        st.info("Todavía no te has postulado a ninguna vacante.")
        return

    for postulacion in resultado:
        with st.container(border=True):
            st.subheader(postulacion["Cargo"])
            st.write(f"**{postulacion['Empresa']}** · {postulacion['Ubicacion']}")
            st.write(f"Estado: **{etiqueta_estado(postulacion['Estado'])}**")
            st.caption(f"Te postulaste el {postulacion['Fecha_postulacion']:%d/%m/%Y}")
            mostrar_informacion_vacante(postulacion)
            with st.expander("Carta de presentación"):
                seccion_carta(postulacion["Id_postulacion"])
            with st.expander("Formulario de la vacante"):
                seccion_formulario(postulacion["Id_postulacion"])
