import streamlit as st

from LoginFront import mostrar_pantalla_login
from CargarCV import mostrar_pantalla_perfil
from VacantesFront import mostrar_pantalla_vacantes
from PostulacionesFront import mostrar_panel_postulaciones
from RecomendacionesFront import mostrar_pantalla_recomendaciones
from GuardadasFront import mostrar_pantalla_guardadas


st.set_page_config(
    page_title="Progent",
    page_icon="💼",
    layout="centered",
)


if "usuario_logueado" not in st.session_state:
    st.session_state["usuario_logueado"] = None

if "modo_perfil" not in st.session_state:
    st.session_state["modo_perfil"] = None


if st.session_state["usuario_logueado"] is None:
    mostrar_pantalla_login()
else:
    seccion = st.sidebar.radio(
        "Menú",
        ["Mi perfil", "Vacantes", "Recomendaciones", "Guardadas", "Mis postulaciones"],
        key="seccion",
    )

    if seccion == "Vacantes":
        mostrar_pantalla_vacantes()
    elif seccion == "Recomendaciones":
        mostrar_pantalla_recomendaciones()
    elif seccion == "Guardadas":
        mostrar_pantalla_guardadas()
    elif seccion == "Mis postulaciones":
        mostrar_panel_postulaciones()
    else:
        mostrar_pantalla_perfil()
