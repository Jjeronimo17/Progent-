import streamlit as st

from LoginFront import mostrar_pantalla_login
from CargarCV import mostrar_pantalla_perfil
from VacantesFront import mostrar_pantalla_vacantes
from PostulacionesFront import mostrar_panel_postulaciones
from RecomendacionesFront import mostrar_pantalla_recomendaciones
from GuardadasFront import mostrar_pantalla_guardadas
from NotificacionesFront import mostrar_pantalla_notificaciones
from alertas import revisarAlertas
from entrevistas import consultarRecordatorios, cuandoEs, textoFecha


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
    # Cada vez que el usuario usa Progent se revisa su alerta (no hay procesos en
    # segundo plano). Si falla, el menú se muestra sin el contador.
    exito, sin_leer = revisarAlertas(st.session_state["usuario_logueado"])
    sin_leer = sin_leer if exito else 0

    seccion = st.sidebar.radio(
        "Menú",
        ["Mi perfil", "Vacantes", "Recomendaciones", "Guardadas", "Mis postulaciones", "Notificaciones"],
        format_func=lambda opcion: f"Notificaciones ({sin_leer})"
        if opcion == "Notificaciones" and sin_leer
        else opcion,
        key="seccion",
    )

    # Recordatorio de las entrevistas que se acercan (#28). Si falla, no se muestra.
    exito, recordatorios = consultarRecordatorios(st.session_state["usuario_logueado"])
    if exito and recordatorios:
        st.sidebar.markdown("**Recordatorios**")
        for r in recordatorios:
            st.sidebar.warning(
                f"Tu entrevista es {cuandoEs(r['Fecha_entrevista'])}: «{r['Cargo']}» en "
                f"{r['Empresa']}, el {textoFecha(r['Fecha_entrevista'])}.",
                icon="📅",
            )

    if seccion == "Vacantes":
        mostrar_pantalla_vacantes()
    elif seccion == "Recomendaciones":
        mostrar_pantalla_recomendaciones()
    elif seccion == "Guardadas":
        mostrar_pantalla_guardadas()
    elif seccion == "Notificaciones":
        mostrar_pantalla_notificaciones()
    elif seccion == "Mis postulaciones":
        mostrar_panel_postulaciones()
    else:
        mostrar_pantalla_perfil()
