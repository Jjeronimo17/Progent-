from datetime import date, datetime

import streamlit as st

from documentos import consultarCarta, guardarCarta
from entrevistas import guardarEntrevista, quitarEntrevista, textoFecha
from formularios import consultarRespuestas, generarRespuestas, guardarRespuestas, leerFormulario
from postulaciones import ESTADOS, cambiarEstado, consultarPostulaciones, deshacerUltimoCambio

# En la base los estados van sin tilde, como los demás ENUM del modelo.
ETIQUETAS_ESTADO = {"En revision": "En revisión"}


def etiqueta_estado(estado):
    return ETIQUETAS_ESTADO.get(estado, estado)


def mostrar_informacion_vacante(postulacion):
    with st.expander("Ver información de la vacante", key=f"exp_info_{postulacion['Id_postulacion']}"):
        st.write(
            f"Estado actual: **{etiqueta_estado(postulacion['Estado'])}** · última actualización "
            f"el {postulacion['Fecha_actualizacion']:%d/%m/%Y a las %H:%M}"
        )
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


def guardar_estado(id_postulacion, cargo):
    # Se ejecuta con on_click: lee el selector y guarda el nuevo estado.
    nuevo = st.session_state[f"estado_{id_postulacion}"]
    exito, mensaje = cambiarEstado(st.session_state["usuario_logueado"], id_postulacion, nuevo)
    if exito:
        # La tarjeta cambia de grupo (#23), así que el aviso va arriba del panel.
        st.session_state["mensaje_panel_estado"] = (
            f"Estado actualizado a «{etiqueta_estado(nuevo)}». «{cargo}» ahora aparece en esa etapa.")
    else:
        st.session_state[f"mensaje_estado_{id_postulacion}"] = (exito, mensaje)


def deshacer_estado(id_postulacion, cargo, anterior):
    exito, mensaje = deshacerUltimoCambio(st.session_state["usuario_logueado"], id_postulacion)
    if exito:
        st.session_state["mensaje_panel_estado"] = (
            f"{mensaje} «{cargo}» volvió a «{etiqueta_estado(anterior)}».")
    else:
        st.session_state[f"mensaje_estado_{id_postulacion}"] = (exito, mensaje)


def seccion_estado(postulacion):
    """Cambiar a mano la etapa de la postulación y deshacer el último cambio (#22)."""
    id_postulacion = postulacion["Id_postulacion"]
    mensaje = st.session_state.pop(f"mensaje_estado_{id_postulacion}", None)
    if mensaje:
        exito, texto = mensaje
        (st.success if exito else st.warning)(texto)
    # El selector arranca en el estado guardado y se reinicia solo cuando ese estado
    # cambia (al guardar o deshacer); así no se pierde lo que el usuario está eligiendo.
    clave, base = f"estado_{id_postulacion}", f"estado_base_{id_postulacion}"
    if clave not in st.session_state or st.session_state.get(base) != postulacion["Estado"]:
        st.session_state[clave] = postulacion["Estado"]
        st.session_state[base] = postulacion["Estado"]
    st.selectbox("Nueva etapa", ESTADOS, format_func=etiqueta_estado, key=clave)
    st.button("Guardar estado", key=f"guardar_estado_{id_postulacion}",
              on_click=guardar_estado, args=(id_postulacion, postulacion["Cargo"]))
    anterior = postulacion["Estado_para_deshacer"]
    if anterior:
        st.button(
            f"Deshacer último cambio (volver a «{etiqueta_estado(anterior)}»)",
            key=f"deshacer_estado_{id_postulacion}",
            on_click=deshacer_estado,
            args=(id_postulacion, postulacion["Cargo"], anterior),
        )


def seccion_entrevista(postulacion):
    """Informar la fecha de la próxima entrevista para que Progent la recuerde (#28)."""
    id_postulacion = postulacion["Id_postulacion"]
    correo = st.session_state["usuario_logueado"]
    mensaje = st.session_state.pop(f"mensaje_entrevista_{id_postulacion}", None)
    if mensaje:
        exito, texto = mensaje
        (st.success if exito else st.error)(texto)

    entrevista = postulacion["Fecha_entrevista"]
    if entrevista:
        st.write(f"Entrevista informada: **{textoFecha(entrevista)}**")

    with st.form(f"form_entrevista_{id_postulacion}"):
        dia = st.date_input("Fecha de la entrevista", value=None, min_value=date.today(), format="DD/MM/YYYY")
        hora = st.time_input("Hora", value=None, step=900)
        guardar = st.form_submit_button("Guardar entrevista")
    if guardar:
        if dia is None or hora is None:
            st.error("Elige la fecha y la hora de la entrevista.")
        else:
            exito, texto = guardarEntrevista(correo, id_postulacion, datetime.combine(dia, hora))
            st.session_state[f"mensaje_entrevista_{id_postulacion}"] = (exito, texto)
            st.rerun()

    if entrevista and st.button("Quitar entrevista", key=f"quitar_entrevista_{id_postulacion}"):
        st.session_state[f"mensaje_entrevista_{id_postulacion}"] = quitarEntrevista(correo, id_postulacion)
        st.rerun()


def mostrar_panel_postulaciones():
    st.title("Mis postulaciones")

    aviso = st.session_state.pop("mensaje_panel_estado", None)
    if aviso:
        st.success(aviso)

    exito, resultado = consultarPostulaciones(st.session_state["usuario_logueado"])

    if not exito:
        st.error(resultado)
        return

    if not resultado:
        st.info("Todavía no te has postulado a ninguna vacante.")
        return

    # Agrupadas por etapa, en el orden del proceso (#23). Dentro de cada etapa, la
    # más reciente primero. Al cambiar el estado, la postulación pasa sola de grupo.
    por_etapa = {etapa: [] for etapa in ESTADOS}
    for postulacion in resultado:
        por_etapa[postulacion["Estado"]].append(postulacion)

    for etapa in ESTADOS:
        st.markdown(f"#### {etiqueta_estado(etapa)} ({len(por_etapa[etapa])})")
        if not por_etapa[etapa]:
            st.caption("Sin postulaciones en esta etapa.")
        for postulacion in por_etapa[etapa]:
            mostrar_tarjeta_postulacion(postulacion)


def mostrar_tarjeta_postulacion(postulacion):
    with st.container(border=True):
        st.subheader(postulacion["Cargo"])
        st.write(f"**{postulacion['Empresa']}** · {postulacion['Ubicacion']}")
        st.write(f"Estado: **{etiqueta_estado(postulacion['Estado'])}**")
        st.caption(f"Te postulaste el {postulacion['Fecha_postulacion']:%d/%m/%Y}")
        st.caption(
            f"Hoja de vida: {postulacion['Cv']}" if postulacion["Cv"] else "Sin hoja de vida asociada"
        )
        entrevista = postulacion["Fecha_entrevista"]
        if entrevista and entrevista >= datetime.now():
            st.caption(f"📅 Próxima entrevista: {textoFecha(entrevista)}")
        elif entrevista:
            # Pasó sin que el usuario la actualizara: ya no está pendiente (#28).
            st.caption(
                f"La entrevista del {textoFecha(entrevista)} ya pasó. Actualiza el estado "
                "o informa una nueva fecha."
            )
        # Los expanders llevan la llave de la postulación: así, cuando la tarjeta cambia
        # de etapa, lo que estaba abierto se va con ella y no queda abierto en otra.
        id_postulacion = postulacion["Id_postulacion"]
        mostrar_informacion_vacante(postulacion)
        with st.expander("Actualizar estado", key=f"exp_estado_{id_postulacion}"):
            seccion_estado(postulacion)
        with st.expander("Informar entrevista", key=f"exp_entrevista_{id_postulacion}"):
            seccion_entrevista(postulacion)
        with st.expander("Carta de presentación", key=f"exp_carta_{id_postulacion}"):
            seccion_carta(id_postulacion)
        with st.expander("Formulario de la vacante", key=f"exp_formulario_{id_postulacion}"):
            seccion_formulario(id_postulacion)
