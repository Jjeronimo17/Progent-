from datetime import date

import streamlit as st

from datosUsuario import (
    añadirDatos,
    añadirEducacion,
    añadirExperiencia,
    consultarDatos,
    consultarEducacion,
    consultarExperiencia,
)

MODALIDADES = ["Sin especificar", "Hibrido", "Presencial", "Virtual"]
ESTADOS_ESTUDIO = ["Cursando", "Graduado", "Aplazado", "Incompleto"]
FECHA_MINIMA = date(1950, 1, 1)


def texto_o_none(valor):
    valor = (valor or "").strip()
    return valor or None


def campos_vacios(campos):
    return [nombre for nombre, valor in campos.items() if not valor or not str(valor).strip()]


def guardar_y_recargar(mensaje, contador=None):
    """Guarda el mensaje de éxito para mostrarlo después de recargar la página.

    Si llega un contador, lo incrementa para que el formulario vuelva a salir vacío.
    """
    st.session_state["mensaje_perfil"] = mensaje
    if contador:
        st.session_state[contador] = st.session_state.get(contador, 0) + 1
    st.rerun()


def seccion_datos_basicos(correo):
    st.subheader("Datos básicos")
    exito, datos = consultarDatos(correo)

    if not exito:
        st.error(datos)
        return

    if datos:
        # Columnas de informacion_usuarios: Correos, Nombre, Edad, Telefono,
        # Correo_contacto, Ubicacion, Ocupacion
        with st.container(border=True):
            st.write(f"**{datos[1]}**")
            st.write(datos[6] or "")
            st.caption(f"{datos[5]} · {datos[4]}" + (f" · {datos[3]}" if datos[3] else ""))
        return

    with st.form("form_datos_basicos"):
        nombre = st.text_input("Nombre completo *", max_chars=60)
        edad = st.number_input("Edad", min_value=14, max_value=100, value=None, step=1)
        telefono = st.text_input("Teléfono", max_chars=50)
        correo_contacto = st.text_input("Correo de contacto *", value=correo, max_chars=200)
        ubicacion = st.text_input("Ubicación *", placeholder="Ciudad, país", max_chars=100)
        ocupacion = st.text_input(
            "Ocupación *", placeholder="Ej.: Estudiante de Ingeniería de Sistemas"
        )
        guardar = st.form_submit_button("Guardar datos básicos")

    if guardar:
        faltan = campos_vacios(
            {
                "Nombre completo": nombre,
                "Correo de contacto": correo_contacto,
                "Ubicación": ubicacion,
                "Ocupación": ocupacion,
            }
        )
        if faltan:
            st.error("Completa los campos obligatorios: " + ", ".join(faltan) + ".")
            return
        if "@" not in correo_contacto:
            st.error("Escribe un correo de contacto válido.")
            return

        exito, mensaje = añadirDatos(
            correo,
            nombre.strip(),
            edad,
            texto_o_none(telefono),
            correo_contacto.strip(),
            ubicacion.strip(),
            ocupacion.strip(),
        )
        if exito:
            guardar_y_recargar(mensaje)
        else:
            st.error(mensaje)


def seccion_experiencia(correo):
    st.subheader("Experiencia laboral")
    exito, experiencias = consultarExperiencia(correo)

    if not exito:
        st.error(experiencias)
    elif not experiencias:
        st.caption("Todavía no has agregado experiencia laboral.")
    else:
        # Columnas de Experiencia: ID, Correos_experiencia, Nombre_empresa, Sector_industria,
        # Tamaño_empresa, Titulo_puesto, Nivel_seniority, Fecha_inicio, Fecha_finalizacion, ...
        for exp in experiencias:
            fin = f"{exp[8]:%m/%Y}" if exp[8] else "actual"
            st.write(f"- **{exp[5]}** en {exp[2]} ({exp[7]:%m/%Y} a {fin})")

    numero = st.session_state.get("formularios_experiencia", 0)
    with st.expander("Agregar experiencia"):
        with st.form(f"form_experiencia_{numero}"):
            empresa = st.text_input("Empresa *", max_chars=100)
            cargo = st.text_input("Cargo *", max_chars=100)
            inicio = st.date_input(
                "Fecha de inicio *", value=None, min_value=FECHA_MINIMA, max_value=date.today()
            )
            fin = st.date_input(
                "Fecha de finalización",
                value=None,
                min_value=FECHA_MINIMA,
                max_value=date.today(),
                help="Déjala vacía si todavía trabajas aquí.",
            )
            funciones = st.text_area("Descripción de funciones *")
            habilidades = st.text_input("Habilidades *", placeholder="Separadas por comas")
            logros = st.text_area("Logros")
            ubicacion = st.text_input("Ubicación de la empresa", max_chars=100)
            modalidad = st.selectbox("Modalidad", MODALIDADES)
            agregar = st.form_submit_button("Guardar experiencia")

        if agregar:
            faltan = campos_vacios(
                {
                    "Empresa": empresa,
                    "Cargo": cargo,
                    "Fecha de inicio": inicio,
                    "Descripción de funciones": funciones,
                    "Habilidades": habilidades,
                }
            )
            if faltan:
                st.error("Completa los campos obligatorios: " + ", ".join(faltan) + ".")
                return

            exito, mensaje = añadirExperiencia(
                correo,
                empresa.strip(),
                None,
                None,
                cargo.strip(),
                None,
                inicio,
                funciones.strip(),
                texto_o_none(logros),
                habilidades.strip(),
                texto_o_none(ubicacion),
                None,
                None if modalidad == MODALIDADES[0] else modalidad,
                fecha_finalizacion=fin,
            )
            if exito:
                guardar_y_recargar(mensaje, "formularios_experiencia")
            else:
                st.error(mensaje)


def seccion_educacion(correo):
    st.subheader("Educación")
    exito, estudios = consultarEducacion(correo)

    if not exito:
        st.error(estudios)
    elif not estudios:
        st.caption("Todavía no has agregado educación.")
    else:
        # Columnas de Educacion: Id_educacion, Correos_educacion, Institucion_educativa,
        # Tipo_institucion, Titulo_Carrera_Grado, Nivel_educacion, Campo_estudio,
        # Fecha_inicio, Fecha_final, Estado_estudio, Logros
        for edu in estudios:
            st.write(f"- **{edu[4]}** en {edu[2]} ({edu[9]}, desde {edu[7]:%m/%Y})")

    numero = st.session_state.get("formularios_educacion", 0)
    with st.expander("Agregar educación"):
        with st.form(f"form_educacion_{numero}"):
            institucion = st.text_input("Institución *", max_chars=100)
            titulo = st.text_input("Título o carrera *", max_chars=200)
            nivel = st.text_input("Nivel", placeholder="Ej.: Pregrado", max_chars=150)
            campo = st.text_input("Campo de estudio", max_chars=200)
            inicio = st.date_input(
                "Fecha de inicio *", value=None, min_value=FECHA_MINIMA, max_value=date.today()
            )
            fin = st.date_input(
                "Fecha de finalización",
                value=None,
                min_value=FECHA_MINIMA,
                help="Déjala vacía si todavía estudias aquí.",
            )
            estado = st.selectbox("Estado *", ESTADOS_ESTUDIO)
            logros = st.text_area("Logros")
            agregar = st.form_submit_button("Guardar educación")

        if agregar:
            faltan = campos_vacios(
                {"Institución": institucion, "Título o carrera": titulo, "Fecha de inicio": inicio}
            )
            if faltan:
                st.error("Completa los campos obligatorios: " + ", ".join(faltan) + ".")
                return

            exito, mensaje = añadirEducacion(
                correo,
                institucion.strip(),
                None,
                titulo.strip(),
                texto_o_none(nivel),
                texto_o_none(campo),
                inicio,
                estado,
                texto_o_none(logros),
                fecha_final=fin,
            )
            if exito:
                guardar_y_recargar(mensaje, "formularios_educacion")
            else:
                st.error(mensaje)


def mostrar_formulario_perfil(correo):
    mensaje = st.session_state.pop("mensaje_perfil", None)
    if mensaje:
        st.success(mensaje)

    seccion_datos_basicos(correo)
    st.divider()
    seccion_experiencia(correo)
    st.divider()
    seccion_educacion(correo)
