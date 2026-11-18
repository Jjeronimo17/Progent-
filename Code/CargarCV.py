import streamlit as st

from datosUsuario import consultarArchivo
from GenerarCvFront import mostrar_generar_cv
from ImportarPerfilFront import mostrar_importar_linkedin, mostrar_subir_cv
from MejorasCvFront import mostrar_mejorar_cv
from PerfilFront import mostrar_formulario_perfil


def mostrar_eleccion_perfil():
    st.title("¿Cómo quieres empezar tu perfil?")
    st.write(
        "El agente construirá tu perfil a partir de lo que elijas. "
        "Podrás editarlo todo después."
    )

    opciones = [
        (
            "linkedin",
            "Importar desde LinkedIn",
            "Sube el PDF de tu perfil (en LinkedIn: Más → Guardar en PDF) y el agente lo lee.",
        ),
        (
            "cv",
            "Subir mi hoja de vida (PDF o Word)",
            "Guárdala en tu perfil y, si quieres, el agente extrae tus datos.",
        ),
        ("manual", "Llenar mi perfil manualmente", "Escribe tus datos paso a paso."),
        (
            "mejorar",
            "Mejorar mi hoja de vida",
            "El agente compara tu perfil con las vacantes que te interesan y te sugiere mejoras.",
        ),
        (
            "generar",
            "Generar mi CV",
            "El agente redacta tu CV a partir de tu perfil, listo para descargar o para postularte.",
        ),
    ]

    for clave, titulo, descripcion in opciones:
        with st.container(border=True):
            st.subheader(titulo)
            st.caption(descripcion)
            if clave == "cv":
                # La hoja de vida guardada queda visible al volver a Mi perfil (#5).
                exito, cv = consultarArchivo(st.session_state["usuario_logueado"])
                if exito and cv:
                    st.caption(f"Hoja de vida guardada: {cv[1]}")
            if st.button("Continuar", key=f"opcion_{clave}", use_container_width=True):
                st.session_state["modo_perfil"] = clave
                st.rerun()

    st.divider()
    if st.button("Cerrar sesión"):
        st.session_state["usuario_logueado"] = None
        st.session_state["modo_perfil"] = None
        st.rerun()


def mostrar_llenar_manual():
    st.title("Llena tu perfil")
    st.caption("Los campos con * son obligatorios.")
    mostrar_formulario_perfil(st.session_state["usuario_logueado"])

    st.divider()
    if st.button("← Volver"):
        st.session_state["modo_perfil"] = None
        st.rerun()


def mostrar_pantalla_mejorar():
    mostrar_mejorar_cv()

    st.divider()
    if st.button("← Volver"):
        st.session_state["modo_perfil"] = None
        st.rerun()


def mostrar_pantalla_generar():
    mostrar_generar_cv()

    st.divider()
    if st.button("← Volver"):
        st.session_state["modo_perfil"] = None
        st.rerun()


def mostrar_pantalla_perfil():
    modo = st.session_state["modo_perfil"]

    if modo is None:
        mostrar_eleccion_perfil()
    elif modo == "linkedin":
        mostrar_importar_linkedin()
    elif modo == "cv":
        mostrar_subir_cv()
    elif modo == "manual":
        mostrar_llenar_manual()
    elif modo == "mejorar":
        mostrar_pantalla_mejorar()
    elif modo == "generar":
        mostrar_pantalla_generar()