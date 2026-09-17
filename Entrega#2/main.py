import streamlit as st

from LoginFront import mostrar_pantalla_login
from CargarCV import mostrar_pantalla_perfil


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
    mostrar_pantalla_perfil()