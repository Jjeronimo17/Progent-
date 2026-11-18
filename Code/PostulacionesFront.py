import streamlit as st

from postulaciones import consultarPostulaciones

# En la base los estados van sin tilde, como los demás ENUM del modelo.
ETIQUETAS_ESTADO = {"En revision": "En revisión"}


def etiqueta_estado(estado):
    return ETIQUETAS_ESTADO.get(estado, estado)


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
