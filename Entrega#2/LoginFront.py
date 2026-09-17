import streamlit as st

from login import iniciarSesion, guardarDataBase


def mostrar_logo():
    izquierda, centro, derecha = st.columns([1, 2, 1])
    with centro:
        st.markdown(
            "<div style='border:1px solid #bbb; background:#eee; "
            "height:70px; display:flex; align-items:center; "
            "justify-content:center; color:#666;'>logo Progent</div>",
            unsafe_allow_html=True,
        )
        st.caption("Progent")


def formulario_crear_cuenta():
    with st.form("form_registro"):
        correo = st.text_input("Correo electrónico", key="registro_correo")
        contrasena = st.text_input(
            "Contraseña", type="password", key="registro_password"
        )
        crear = st.form_submit_button("Crear cuenta", use_container_width=True)

    if crear:
        if not correo or not contrasena:
            st.error("Completa el correo y la contraseña.")
            return

        if "@" not in correo:
            st.error("Escribe un correo válido.")
            return

        if len(contrasena) < 8:
            st.error("La contraseña debe tener al menos 8 caracteres.")
            return

        exito, mensaje = guardarDataBase(correo, contrasena)
        if exito:
            st.success(mensaje)
        else:
            st.error(mensaje)


def formulario_iniciar_sesion():
    with st.form("form_login"):
        correo = st.text_input("Correo electrónico", key="login_correo")
        contrasena = st.text_input("Contraseña", type="password", key="login_password")
        entrar = st.form_submit_button("Iniciar sesión", use_container_width=True)

    if entrar:
        if not correo or not contrasena:
            st.error("Escribe tu correo y tu contraseña.")
            return

        if iniciarSesion(correo, contrasena):
            st.session_state["usuario_logueado"] = correo
            st.rerun()
        else:
            st.error("Correo o contraseña incorrectos.")


def mostrar_opciones_alternas():
    st.markdown(
        "<p style='text-align:center; color:#888; margin:8px 0;'>— o —</p>",
        unsafe_allow_html=True,
    )

    st.button(
        "Continuar con Google / LinkedIn",
        use_container_width=True,
        disabled=True,
        help="Pendiente: requiere configurar OAuth con Google y LinkedIn.",
    )

    st.markdown(
        "<p style='text-align:center; margin-top:12px;'>"
        "<a href='#' style='color:#666; font-size:0.9em;'>"
        "¿Olvidaste tu contraseña?</a></p>",
        unsafe_allow_html=True,
    )


def mostrar_pantalla_login():
    mostrar_logo()

    pestana_crear, pestana_entrar = st.tabs(["Crear cuenta", "Iniciar sesión"])

    with pestana_crear:
        formulario_crear_cuenta()

    with pestana_entrar:
        formulario_iniciar_sesion()

    mostrar_opciones_alternas()
