"""Pantallas para subir la hoja de vida e importar el perfil con el agente (#4, #5 y #6)."""

import streamlit as st

from cargarLinkedin import extraerPerfilLinkedin
from datosUsuario import consultarArchivo
from documentos import guardarHojaDeVida
from importarPerfil import extraerPerfil, guardarPerfilImportado


def correo_actual():
    return st.session_state["usuario_logueado"]


def ir_a_mi_perfil():
    st.session_state["modo_perfil"] = "manual"


def mostrar_mensaje(origen):
    mensaje = st.session_state.pop(f"mensaje_importar_{origen}", None)
    if mensaje:
        exito, texto = mensaje
        (st.success if exito else st.error)(texto)
        if exito and texto.startswith("Guardaste tu perfil"):
            st.button("Ver mi perfil", key=f"ver_perfil_{origen}", on_click=ir_a_mi_perfil)


def seccion_hoja_guardada():
    """La hoja de vida del perfil queda visible para descargarla o reemplazarla (#5)."""
    exito, cv = consultarArchivo(correo_actual())
    if not exito:
        st.error(cv)
        return
    if cv is None:
        st.caption("Todavía no tienes una hoja de vida guardada en tu perfil.")
        return
    # Columnas de archivos_usuarios: Correos_usuarios, nombre_archivo, tipo, archivo_bytes
    with st.container(border=True):
        st.markdown(f"Hoja de vida guardada en tu perfil: **{cv[1]}**")
        st.download_button("Descargar mi hoja de vida", data=cv[3], file_name=cv[1], mime=cv[2])
        st.caption("Para reemplazarla, sube otra abajo y pulsa «Guardar en mi perfil».")


def pedir_extraccion(origen, archivo):
    with st.spinner("El agente está leyendo tu archivo..."):
        if origen == "linkedin":
            exito, datos = extraerPerfilLinkedin(correo_actual(), archivo.name, archivo.getvalue())
        else:
            exito, datos = extraerPerfil(correo_actual(), archivo.name, archivo.getvalue(), "cv")
    ronda = st.session_state.get("ronda_importar", 0) + 1
    st.session_state["ronda_importar"] = ronda
    if exito and datos["borrador"]:
        st.session_state[f"importacion_{origen}"] = {"borrador": datos["borrador"], "ronda": ronda}
    else:
        st.session_state.pop(f"importacion_{origen}", None)
        st.session_state[f"resultado_importar_{origen}"] = (exito, datos)


def mostrar_resultado_fallido(origen):
    respuesta = st.session_state.pop(f"resultado_importar_{origen}", None)
    if respuesta is None:
        return
    exito, datos = respuesta
    if not exito:
        st.error(datos)
        return
    # PDF sin texto (por ejemplo, un escaneo): no hay nada que extraer (#6).
    st.warning(
        "No pude extraer información: el PDF no tiene texto seleccionable (puede ser un "
        "escaneo). Completa tu perfil manualmente o sube otra versión del archivo."
    )
    st.button("Llenar mi perfil manualmente", key=f"manual_{origen}", on_click=ir_a_mi_perfil)


def leer_borrador(origen, importacion):
    """El borrador con lo que el usuario dejó en pantalla."""
    s, r, b = st.session_state, importacion["ronda"], importacion["borrador"]
    clave = lambda nombre: f"imp_{origen}_{r}_{nombre}"
    nuevo = {campo: s.get(clave(campo), b[campo]).strip() for campo in ("nombre", "titular", "correo", "telefono", "ciudad")}
    nuevo["experiencia"] = []
    for i, e in enumerate(b["experiencia"]):
        if not s.get(clave(f"exp_{i}_incluir"), True):
            continue
        nuevo["experiencia"].append({
            "cargo": s.get(clave(f"exp_{i}_cargo"), e["cargo"]).strip(),
            "empresa": s.get(clave(f"exp_{i}_empresa"), e["empresa"]).strip(),
            "fecha_inicio": s.get(clave(f"exp_{i}_inicio"), e["fecha_inicio"]).strip(),
            "fecha_fin": s.get(clave(f"exp_{i}_fin"), e["fecha_fin"]).strip(),
            "actual": s.get(clave(f"exp_{i}_actual"), e["actual"]),
            "descripcion": s.get(clave(f"exp_{i}_descripcion"), e["descripcion"]).strip(),
        })
    nuevo["educacion"] = []
    for i, e in enumerate(b["educacion"]):
        if not s.get(clave(f"edu_{i}_incluir"), True):
            continue
        nuevo["educacion"].append({
            "titulo": s.get(clave(f"edu_{i}_titulo"), e["titulo"]).strip(),
            "institucion": s.get(clave(f"edu_{i}_institucion"), e["institucion"]).strip(),
            "fecha_inicio": s.get(clave(f"edu_{i}_inicio"), e["fecha_inicio"]).strip(),
            "fecha_fin": s.get(clave(f"edu_{i}_fin"), e["fecha_fin"]).strip(),
            "en_curso": s.get(clave(f"edu_{i}_en_curso"), e["en_curso"]),
        })
    texto = s.get(clave("habilidades"), ", ".join(b["habilidades"]))
    nuevo["habilidades"] = [h.strip() for h in texto.split(",") if h.strip()]
    nuevo["idiomas"] = b["idiomas"]
    return nuevo


def confirmar(origen):
    importacion = st.session_state[f"importacion_{origen}"]
    if importacion["borrador"]["dudosos"] and not st.session_state.get(f"imp_{origen}_{importacion['ronda']}_revise"):
        st.session_state[f"mensaje_importar_{origen}"] = (
            False, "Confirma que revisaste los datos que el agente marcó como dudosos.")
        return
    exito, mensaje = guardarPerfilImportado(correo_actual(), leer_borrador(origen, importacion))
    st.session_state[f"mensaje_importar_{origen}"] = (exito, mensaje)
    if exito:
        st.session_state.pop(f"importacion_{origen}")


def rechazar(origen):
    st.session_state.pop(f"importacion_{origen}", None)
    st.session_state[f"mensaje_importar_{origen}"] = (True, "Rechazaste la propuesta del agente: tu perfil no cambió.")


def seccion_revision(origen):
    """Revisar, editar, rechazar o confirmar lo que propuso el agente (#4 y #6)."""
    importacion = st.session_state.get(f"importacion_{origen}")
    if importacion is None:
        return
    b, r = importacion["borrador"], importacion["ronda"]
    clave = lambda nombre: f"imp_{origen}_{r}_{nombre}"

    st.markdown("**Revisa lo que encontró el agente**")
    st.caption("Nada se guarda hasta que confirmes. Corrige lo que esté mal o desmarca lo que no quieras guardar.")
    if b["dudosos"]:
        st.warning(
            "El agente no quedó seguro de: " + ", ".join(b["dudosos"])
            + ". Quedan pendientes de tu confirmación."
        )

    with st.container(border=True):
        st.markdown("**Datos básicos**")
        st.text_input("Nombre completo *", value=b["nombre"], key=clave("nombre"))
        st.text_input("Titular u ocupación", value=b["titular"], key=clave("titular"))
        st.text_input("Correo de contacto *", value=b["correo"], key=clave("correo"))
        st.text_input("Teléfono", value=b["telefono"], key=clave("telefono"))
        st.text_input("Ciudad *", value=b["ciudad"], key=clave("ciudad"))

    st.markdown("**Experiencia**")
    if not b["experiencia"]:
        st.caption("El agente no encontró experiencia laboral.")
    for i, e in enumerate(b["experiencia"]):
        with st.container(border=True):
            st.checkbox(f"Incluir: {e['cargo'] or 'sin cargo'} — {e['empresa'] or 'sin empresa'}", value=True,
                        key=clave(f"exp_{i}_incluir"))
            izquierda, derecha = st.columns(2)
            izquierda.text_input("Cargo *", value=e["cargo"], key=clave(f"exp_{i}_cargo"))
            derecha.text_input("Empresa *", value=e["empresa"], key=clave(f"exp_{i}_empresa"))
            izquierda.text_input("Fecha de inicio * (AAAA-MM-DD)", value=e["fecha_inicio"], key=clave(f"exp_{i}_inicio"))
            derecha.text_input("Fecha de fin (AAAA-MM-DD)", value=e["fecha_fin"], key=clave(f"exp_{i}_fin"))
            st.checkbox("Trabajo aquí actualmente", value=e["actual"], key=clave(f"exp_{i}_actual"))
            st.text_area("Descripción de funciones", value=e["descripcion"], key=clave(f"exp_{i}_descripcion"))

    st.markdown("**Educación**")
    if not b["educacion"]:
        st.caption("El agente no encontró estudios.")
    for i, e in enumerate(b["educacion"]):
        with st.container(border=True):
            st.checkbox(f"Incluir: {e['titulo'] or 'sin título'} — {e['institucion'] or 'sin institución'}", value=True,
                        key=clave(f"edu_{i}_incluir"))
            izquierda, derecha = st.columns(2)
            izquierda.text_input("Título *", value=e["titulo"], key=clave(f"edu_{i}_titulo"))
            derecha.text_input("Institución *", value=e["institucion"], key=clave(f"edu_{i}_institucion"))
            izquierda.text_input("Fecha de inicio * (AAAA-MM-DD)", value=e["fecha_inicio"], key=clave(f"edu_{i}_inicio"))
            derecha.text_input("Fecha de fin (AAAA-MM-DD)", value=e["fecha_fin"], key=clave(f"edu_{i}_fin"))
            st.checkbox("Lo estoy cursando", value=e["en_curso"], key=clave(f"edu_{i}_en_curso"))

    st.text_area("Habilidades (separadas por comas)", value=", ".join(b["habilidades"]), key=clave("habilidades"))
    if b["idiomas"]:
        st.caption("Idiomas: " + ", ".join(
            i["idioma"] + (f" ({i['nivel']})" if i["nivel"] else "") for i in b["idiomas"]))

    if b["dudosos"]:
        st.checkbox("Revisé los datos que el agente marcó como dudosos", key=clave("revise"))
    izquierda, derecha = st.columns(2)
    izquierda.button("Confirmar y guardar en mi perfil", key=clave("confirmar"), type="primary",
                     use_container_width=True, on_click=confirmar, args=(origen,))
    derecha.button("Rechazar", key=clave("rechazar"), use_container_width=True, on_click=rechazar, args=(origen,))


def mostrar_subir_cv():
    st.title("Sube tu hoja de vida")
    st.caption("PDF o Word (.docx), máximo 5 MB.")
    mostrar_mensaje("cv")
    seccion_hoja_guardada()

    archivo = st.file_uploader("Arrastra tu hoja de vida aquí", key="archivo_cv")
    if archivo is not None:
        izquierda, derecha = st.columns(2)
        if izquierda.button("Guardar en mi perfil", use_container_width=True):
            st.session_state["mensaje_importar_cv"] = guardarHojaDeVida(
                correo_actual(), archivo.name, archivo.getvalue())
            st.rerun()
        if derecha.button("Extraer mis datos con el agente", type="primary", use_container_width=True):
            pedir_extraccion("cv", archivo)

    mostrar_resultado_fallido("cv")
    seccion_revision("cv")

    if st.button("← Volver"):
        st.session_state["modo_perfil"] = None
        st.rerun()


def mostrar_importar_linkedin():
    st.title("Importar desde LinkedIn")
    st.write(
        "1. En LinkedIn abre tu perfil, elige **Más** y luego **Guardar en PDF**.\n"
        "2. Sube aquí ese PDF. El agente leerá tu experiencia, educación y aptitudes."
    )
    mostrar_mensaje("linkedin")

    archivo = st.file_uploader("Arrastra el PDF de tu perfil de LinkedIn aquí", key="archivo_linkedin")
    if archivo is not None and st.button("Extraer mis datos con el agente", type="primary"):
        pedir_extraccion("linkedin", archivo)

    mostrar_resultado_fallido("linkedin")
    seccion_revision("linkedin")

    if st.button("← Volver"):
        st.session_state["modo_perfil"] = None
        st.rerun()
