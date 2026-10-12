import streamlit as st


def mostrar_eleccion_perfil():
    st.title("¿Cómo quieres empezar tu perfil?")
    st.write(
        "El agente construirá tu perfil a partir de lo que elijas. "
        "Podrás editarlo todo después."
    )

    opciones = [
        ("linkedin", "Importar desde LinkedIn", "Sube el .zip que exporta LinkedIn."),
        ("cv", "Subir mi hoja de vida (PDF)", "El agente extrae tus datos del PDF."),
        ("manual", "Llenar mi perfil manualmente", "Escribe tus datos paso a paso."),
    ]

    for clave, titulo, descripcion in opciones:
        with st.container(border=True):
            st.subheader(titulo)
            st.caption(descripcion)
            if st.button("Continuar", key=f"opcion_{clave}", use_container_width=True):
                st.session_state["modo_perfil"] = clave
                st.rerun()

    st.divider()
    if st.button("Cerrar sesión"):
        st.session_state["usuario_logueado"] = None
        st.session_state["modo_perfil"] = None
        st.rerun()


def mostrar_importar_linkedin():
    st.title("Importar desde LinkedIn")
    st.write(
        "1. Descarga tu archivo de datos desde LinkedIn "
        "(Ajustes → Obtener copia de tus datos).\n"
        "2. Sube aquí el archivo .zip exportado."
    )

    archivo = st.file_uploader("Arrastra el archivo .zip aquí", type="zip")

    if archivo is not None:
        st.success(f"Archivo recibido: {archivo.name}")
        st.info("Pendiente: conectar con el agente que procesa el .zip de LinkedIn.")

    if st.button("← Volver"):
        st.session_state["modo_perfil"] = None
        st.rerun()


def mostrar_subir_cv():
    st.title("Sube tu hoja de vida")
    st.caption("Formato PDF, máx. 10 MB. El agente extraerá tus datos automáticamente.")

    archivo = st.file_uploader("Arrastra tu PDF aquí", type="pdf")

    if archivo is not None:
        st.success(f"Archivo recibido: {archivo.name}")
        st.info("Pendiente: conectar con el agente de graph.py (leer_pdf / extraer).")

    if st.button("← Volver"):
        st.session_state["modo_perfil"] = None
        st.rerun()


def mostrar_llenar_manual():
    st.title("Llena tu perfil")
    st.info("Esta pantalla todavía no está construida (Paso 5 del wireframe).")

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