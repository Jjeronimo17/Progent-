import streamlit as st

from vacantes import consultarVacantes


def mostrar_tarjeta_vacante(vacante):
    with st.container(border=True):
        st.subheader(vacante["Cargo"])
        st.write(f"**{vacante['Empresa']}** · {vacante['Ubicacion']}")

        with st.expander("Ver descripción y requisitos"):
            st.markdown("**Descripción**")
            st.write(vacante["Descripcion"])
            st.markdown("**Requisitos**")
            st.write(vacante["Requisitos"])
            st.caption(f"Publicada el {vacante['Fecha_publicacion']:%d/%m/%Y}")


def mostrar_pantalla_vacantes():
    st.title("Vacantes disponibles")

    exito, resultado = consultarVacantes()

    if not exito:
        st.error(resultado)
        return

    if not resultado:
        st.info("Por ahora no hay vacantes disponibles. Vuelve a revisar más tarde.")
        return

    st.caption(f"{len(resultado)} vacantes disponibles")
    for vacante in resultado:
        mostrar_tarjeta_vacante(vacante)
