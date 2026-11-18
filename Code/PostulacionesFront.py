import streamlit as st

from postulaciones import consultarPostulaciones


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
            st.caption(f"Te postulaste el {postulacion['Fecha_postulacion']:%d/%m/%Y}")
