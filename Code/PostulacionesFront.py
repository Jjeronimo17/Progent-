import streamlit as st

from documentos import consultarCarta, guardarCarta
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
