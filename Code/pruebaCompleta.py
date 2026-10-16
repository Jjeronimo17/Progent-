"""Frontend de PRUEBA para todo el backend de Progent.

Ejecutar desde la raíz del repo:   streamlit run src/pruebaCompleta.py

No modifica ningún archivo existente: solo importa y llama tus funciones.
Cada llamada muestra el resultado interpretado y el valor crudo, y si la función
lanza una excepción, la muestra en pantalla en lugar de tumbar la app.
"""

from datetime import date

import pandas as pd
import streamlit as st

import datosUsuario
import graph
from LoginFront import mostrar_pantalla_login

st.set_page_config(page_title="Progent · Pruebas", page_icon="🧪", layout="wide")

FECHA_MIN, FECHA_MAX = date(1950, 1, 1), date(2100, 12, 31)
MODALIDADES = ["Hibrido", "Presencial", "Virtual"]
ESTADOS_ESTUDIO = ["Cursando", "Graduado", "Aplazado", "Incompleto"]
COLUMNAS_GENERALES = ["Correos", "Nombre", "Edad", "Telefono", "Correo_contacto", "Ubicacion", "Ocupacion"]
COLUMNAS_EXP = [
    "ID", "Correos_experiencia", "Nombre_empresa", "Sector_industria", "Tamaño_empresa",
    "Titulo_puesto", "Nivel_seniority", "Fecha_inicio", "Fecha_finalizacion",
    "Descripcion_funciones", "Logros", "Habilidades", "Ubicacion_empresa",
    "Tipo_contrato", "Modalidad_trabajo",
]
COLUMNAS_EDU = [
    "Id_educacion", "Correos_educacion", "Institucion_educativa", "Tipo_institucion",
    "Titulo_Carrera_grado", "Nivel_educacion", "Campo_Estudio", "Fecha_inicio",
    "Fecha_final", "Estado_Estudio", "Logros",
]


# ===========================================================================
# Utilidades
# ===========================================================================

def llamar(funcion, *args, **kwargs):
    """Llama la función; si lanza excepción, la devuelve en lugar de reventar."""
    try:
        return funcion(*args, **kwargs)
    except Exception as e:
        return e


def mostrar_resultado(resultado, titulo=None):
    """Interpreta (bool, mensaje), bool, None o excepción, y muestra el crudo."""
    if titulo:
        st.caption(titulo)
    if isinstance(resultado, Exception):
        st.error(f"La función lanzó una excepción: {type(resultado).__name__}")
        st.exception(resultado)
        return
    if isinstance(resultado, tuple) and len(resultado) == 2 and isinstance(resultado[0], bool):
        ok, mensaje = resultado
        texto = mensaje if isinstance(mensaje, str) else f"(dato de tipo {type(mensaje).__name__})"
        (st.success if ok else st.error)(texto)
    elif isinstance(resultado, bool):
        (st.success if resultado else st.error)(f"Retornó {resultado}")
    elif resultado is None:
        st.warning("La función retornó None.")
    else:
        st.info(f"Retornó un valor de tipo {type(resultado).__name__}.")
    with st.expander("Valor retornado (crudo)"):
        st.code(repr(resultado)[:3000])


def es_contrato(resultado):
    return isinstance(resultado, tuple) and len(resultado) == 2 and isinstance(resultado[0], bool)


def fecha_opcional(etiqueta, clave, texto_check):
    sin_fecha = st.checkbox(texto_check, key=f"{clave}_sin")
    valor = st.date_input(etiqueta, value=date.today(), min_value=FECHA_MIN,
                          max_value=FECHA_MAX, key=f"{clave}_fecha", disabled=sin_fecha)
    return None if sin_fecha else valor


def tabla_filas(filas, columnas):
    """Muestra una lista de tuplas como tabla con nombres de columna."""
    if not filas:
        st.info("No hay registros.")
        return
    datos = []
    for f in filas:
        if isinstance(f, (tuple, list)) and len(f) == len(columnas):
            datos.append(dict(zip(columnas, f)))
        else:
            datos.append({"fila (columnas no coinciden)": repr(f)})
    st.dataframe(pd.DataFrame(datos).astype(str), use_container_width=True, hide_index=True)


# ===========================================================================
# 1. Datos generales del perfil
# ===========================================================================

def seccion_datos_generales(correo):
    st.header("Datos generales del perfil")
    t_consultar, t_anadir, t_actualizar = st.tabs(["consultarDatos", "añadirDatos", "actualizarPerfil"])

    with t_consultar:
        if st.button("Consultar mis datos", key="btn_consultar_datos"):
            r = llamar(datosUsuario.consultarDatos, correo)
            mostrar_resultado(r)
            if es_contrato(r) and r[0]:
                if r[1] is None:
                    st.info("Este usuario no tiene datos generales todavía.")
                else:
                    tabla_filas([r[1]], COLUMNAS_GENERALES)

    with t_anadir:
        with st.form("form_anadir_datos"):
            nombre = st.text_input("Nombre")
            edad = st.number_input("Edad", min_value=0, max_value=120, value=None, step=1)
            telefono = st.text_input("Teléfono (vacío = None)")
            correo_contacto = st.text_input("Correo de contacto (vacío = None)")
            ubicacion = st.text_input("Ubicación (vacío = None)")
            ocupacion = st.text_input("Ocupación (vacío = None)")
            enviar = st.form_submit_button("añadirDatos")
        if enviar:
            r = llamar(
                datosUsuario.añadirDatos, correo, nombre,
                int(edad) if edad is not None else None,
                telefono or None, correo_contacto or None, ubicacion or None, ocupacion or None,
            )
            mostrar_resultado(r)

    with t_actualizar:
        st.caption("Se precarga con lo que devuelve consultarDatos. Prueba guardar sin cambiar nada.")
        r = llamar(datosUsuario.consultarDatos, correo)
        actual = {}
        if es_contrato(r) and r[0] and r[1]:
            actual = dict(zip(COLUMNAS_GENERALES, r[1]))
        with st.form("form_actualizar"):
            nombre = st.text_input("Nombre", actual.get("Nombre") or "")
            edad = st.number_input("Edad", min_value=0, max_value=120,
                                   value=actual.get("Edad"), step=1)
            telefono = st.text_input("Teléfono", actual.get("Telefono") or "")
            correo_contacto = st.text_input("Correo de contacto", actual.get("Correo_contacto") or "")
            ubicacion = st.text_input("Ubicación", actual.get("Ubicacion") or "")
            ocupacion = st.text_input("Ocupación", actual.get("Ocupacion") or "")
            enviar = st.form_submit_button("actualizarPerfil")
        if enviar:
            r = llamar(
                datosUsuario.actualizarPerfil, correo, nombre, edad, telefono,
                correo_contacto, ubicacion, ocupacion,
            )
            mostrar_resultado(r)


# ===========================================================================
# 2. Experiencia
# ===========================================================================

def seccion_experiencia(correo):
    st.header("Experiencia laboral")
    t_consultar, t_anadir = st.tabs(["consultarExperiencia", "añadirExperiencia"])

    with t_consultar:
        if st.button("Consultar mi experiencia", key="btn_consultar_exp"):
            r = llamar(datosUsuario.consultarExperiencia, correo)
            mostrar_resultado(r)
            if es_contrato(r) and r[0]:
                tabla_filas(r[1], COLUMNAS_EXP)

    with t_anadir:
        st.caption("El formulario no valida fechas: puedes probar una fecha final anterior a la inicial.")
        c1, c2 = st.columns(2)
        with c1:
            nombre_empresa = st.text_input("Nombre de la empresa", key="exp_empresa")
            sector = st.text_input("Sector / industria", key="exp_sector")
            tamano = st.number_input("Tamaño de la empresa", min_value=0, value=None, step=1, key="exp_tam")
            titulo = st.text_input("Título del puesto", key="exp_titulo")
            seniority = st.text_input("Nivel de seniority", key="exp_sen")
            ubicacion_emp = st.text_input("Ubicación de la empresa", key="exp_ubi")
            contrato = st.text_input("Tipo de contrato", key="exp_contrato")
            modalidad = st.selectbox("Modalidad", MODALIDADES, key="exp_mod")
        with c2:
            fecha_inicio = st.date_input("Fecha de inicio", value=date.today(),
                                         min_value=FECHA_MIN, max_value=FECHA_MAX, key="exp_ini")
            fecha_fin = fecha_opcional("Fecha de finalización", "exp_fin", "Trabajo actual (None)")
            descripcion = st.text_area("Descripción de funciones", key="exp_desc")
            logros = st.text_area("Logros", key="exp_logros")
            habilidades = st.text_area("Habilidades", key="exp_hab")
        if st.button("añadirExperiencia", type="primary"):
            r = llamar(
                datosUsuario.añadirExperiencia, correo, nombre_empresa, sector or None,
                int(tamano) if tamano is not None else None, titulo, seniority or None,
                fecha_inicio, descripcion or None, logros or None, habilidades or None,
                ubicacion_emp or None, contrato or None, modalidad, fecha_fin,
            )
            mostrar_resultado(r)


# ===========================================================================
# 3. Educación
# ===========================================================================

def seccion_educacion(correo):
    st.header("Educación")
    t_consultar, t_anadir = st.tabs(["consultarEducacion", "añadirEducacion"])

    with t_consultar:
        if st.button("Consultar mi educación", key="btn_consultar_edu"):
            r = llamar(datosUsuario.consultarEducacion, correo)
            mostrar_resultado(r)
            if es_contrato(r) and r[0]:
                tabla_filas(r[1], COLUMNAS_EDU)

    with t_anadir:
        st.caption("El formulario no valida fechas: puedes probar una fecha final anterior a la inicial.")
        c1, c2 = st.columns(2)
        with c1:
            institucion = st.text_input("Institución educativa", key="edu_inst")
            tipo_inst = st.text_input("Tipo de institución", key="edu_tipo")
            titulo = st.text_input("Título / carrera / grado", key="edu_titulo")
            nivel = st.text_input("Nivel de educación", key="edu_nivel")
            campo = st.text_input("Campo de estudio", key="edu_campo")
        with c2:
            estado = st.selectbox("Estado del estudio", ESTADOS_ESTUDIO, key="edu_estado")
            fecha_inicio = st.date_input("Fecha de inicio", value=date.today(),
                                         min_value=FECHA_MIN, max_value=FECHA_MAX, key="edu_ini")
            fecha_fin = fecha_opcional("Fecha final", "edu_fin", "En curso (None)")
            logros = st.text_area("Logros", key="edu_logros")
        if st.button("añadirEducacion", type="primary"):
            r = llamar(
                datosUsuario.añadirEducacion, correo, institucion, tipo_inst or None,
                titulo, nivel or None, campo or None, fecha_inicio, estado,
                logros or None, fecha_fin,
            )
            mostrar_resultado(r)


# ===========================================================================
# 4. Importar perfil (hoja de vida PDF/Word o LinkedIn) con el grafo
# ===========================================================================

def _editor_generico(datos, dudosos, version):
    editados = {}
    for campo, valor in datos.items():
        if campo == "campos_dudosos":
            continue
        clave = f"imp{version}_{campo}"
        etiqueta = f"⚠️ {campo}" if campo in dudosos else campo
        if isinstance(valor, list) and valor and all(isinstance(x, dict) for x in valor):
            st.markdown(f"**{etiqueta}**")
            tabla = st.data_editor(pd.DataFrame(valor), num_rows="dynamic",
                                   use_container_width=True, key=clave)
            tabla = tabla.astype(object).where(pd.notnull(tabla), None)
            editados[campo] = tabla.to_dict("records")
        elif isinstance(valor, list):
            texto = st.text_area(f"{etiqueta} (uno por línea)",
                                 "\n".join("" if x is None else str(x) for x in valor), key=clave)
            editados[campo] = [l.strip() for l in texto.splitlines() if l.strip()]
        elif isinstance(valor, dict):
            st.markdown(f"**{etiqueta}**")
            sub = {}
            for k, v in valor.items():
                if isinstance(v, list):
                    sub[k] = v
                    st.caption(f"{k}: {v}")
                else:
                    t = st.text_input(f"{campo}.{k}", "" if v is None else str(v), key=f"{clave}_{k}")
                    sub[k] = t or None
            editados[campo] = sub
        elif isinstance(valor, bool):
            editados[campo] = st.checkbox(etiqueta, value=valor, key=clave)
        else:
            t = st.text_input(etiqueta, "" if valor is None else str(valor), key=clave)
            editados[campo] = t or None
    editados["campos_dudosos"] = dudosos
    return editados


def seccion_importar(correo):
    st.header("Importar perfil con el agente")
    st.caption("Grafo de extracción (graph.grafo) + guardado con añadirDatosExtraidos.")

    origen = st.radio("Origen", ["cv", "linkedin"], horizontal=True,
                      format_func=lambda o: "Hoja de vida (PDF o Word)" if o == "cv" else "LinkedIn (PDF)")
    tipos = ["pdf", "docx"] if origen == "cv" else ["pdf"]
    archivo = st.file_uploader("Archivo", type=tipos, key=f"imp_archivo_{origen}")

    if archivo is not None and st.button("Extraer datos", type="primary"):
        tipo = archivo.name.rsplit(".", 1)[-1].lower()
        estado_inicial = {"tipo": tipo, "origen": origen, "errores": []}
        estado_inicial["docx_bytes" if tipo == "docx" else "pdf_bytes"] = archivo.getvalue()
        with st.spinner("El agente está leyendo el documento..."):
            st.session_state["imp_estado"] = llamar(graph.grafo.invoke, estado_inicial)
        st.session_state["imp_version"] = st.session_state.get("imp_version", 0) + 1
        st.session_state.pop("imp_guardado", None)

    estado = st.session_state.get("imp_estado")
    if estado is None:
        return
    if isinstance(estado, Exception):
        mostrar_resultado(estado, "El grafo lanzó una excepción")
        return

    with st.expander("Estado final del grafo (crudo)"):
        st.json({k: (f"<{len(v)} bytes>" if isinstance(v, bytes) else v) for k, v in estado.items()})

    for e in estado.get("errores") or []:
        st.error(e)

    perfil = estado.get("perfil")
    if not isinstance(perfil, dict):
        st.warning("El grafo no dejó un perfil en el estado.")
        return

    dudosos = perfil.get("campos_dudosos") or []
    if dudosos:
        st.warning("El agente no quedó seguro de: " + ", ".join(map(str, dudosos)))

    st.subheader("Revisa y corrige")
    editados = _editor_generico(perfil, dudosos, st.session_state.get("imp_version", 0))

    if st.button("✅ Confirmar y guardar (añadirDatosExtraidos)", type="primary"):
        st.session_state["imp_guardado"] = llamar(datosUsuario.añadirDatosExtraidos, correo, editados)
        st.session_state["imp_enviado"] = editados

    if "imp_guardado" in st.session_state:
        mostrar_resultado(st.session_state["imp_guardado"], "Resultado de añadirDatosExtraidos")
        with st.expander("Diccionario enviado como 'datos'"):
            st.json(st.session_state["imp_enviado"])


# ===========================================================================
# 5. Archivo del CV guardado
# ===========================================================================

def _interpretar_fila_archivo(fila):
    contenido = nombre = mime = None
    for valor in fila:
        if isinstance(valor, (bytes, bytearray, memoryview)):
            contenido = bytes(valor)
        elif isinstance(valor, str):
            if "@" in valor:
                continue
            if "/" in valor and mime is None:
                mime = valor
            elif nombre is None:
                nombre = valor
    return contenido, nombre, mime


def seccion_archivo(correo):
    st.header("Archivo del CV")
    archivo = st.file_uploader("Archivo", type=["pdf", "docx"], key="arch_subir")
    c1, c2 = st.columns(2)
    if c1.button("guardarArchivos", disabled=archivo is None, use_container_width=True):
        mostrar_resultado(llamar(datosUsuario.guardarArchivos, correo, archivo.name, archivo.getvalue()))
    if c2.button("actualizarArchivo", disabled=archivo is None, use_container_width=True):
        mostrar_resultado(llamar(datosUsuario.actualizarArchivo, correo, archivo.name, archivo.getvalue()))

    st.divider()
    st.subheader("consultarArchivo")
    r = llamar(datosUsuario.consultarArchivo, correo)
    if not es_contrato(r) or not r[0]:
        mostrar_resultado(r)
        return
    fila = r[1]
    if fila is None:
        st.info("Este usuario no tiene archivo guardado.")
        return
    with st.expander("Columnas de la fila devuelta"):
        for i, v in enumerate(fila):
            muestra = f"{len(v)} bytes" if isinstance(v, (bytes, bytearray, memoryview)) else repr(v)
            st.write(f"Posición {i}: `{type(v).__name__}` → {muestra}")
    contenido, nombre, mime = _interpretar_fila_archivo(fila)
    if contenido is None:
        st.error("La fila no trae los bytes del archivo.")
        return
    st.write(f"📄 **{nombre}** · {mime} · {len(contenido) / 1024:.1f} KB")
    st.download_button("⬇️ Descargar", data=contenido, file_name=nombre or "cv",
                       mime=mime or "application/octet-stream")


# ===========================================================================
# 6. Generar CV (historia #7)
# ===========================================================================

def _editor_cv(cv, version):
    dudosas = [d.lower() for d in cv.get("secciones_dudosas", [])]
    k = f"cv{version}"
    nombre = st.text_input("Nombre", cv["nombre"], key=f"{k}_n")
    titular = st.text_input("Titular", cv["titular"], key=f"{k}_t")
    c1, c2, c3 = st.columns(3)
    contacto = {
        "correo": c1.text_input("Correo", cv["contacto"]["correo"], key=f"{k}_c"),
        "telefono": c2.text_input("Teléfono", cv["contacto"]["telefono"], key=f"{k}_tel"),
        "ubicacion": c3.text_input("Ubicación", cv["contacto"]["ubicacion"], key=f"{k}_u"),
    }
    resumen = st.text_area(("⚠️ " if "resumen" in dudosas else "") + "Perfil profesional",
                           cv["resumen"], key=f"{k}_r")
    experiencia = []
    for i, e in enumerate(cv["experiencia"]):
        dudosa = f"experiencia {i + 1}" in dudosas
        with st.expander(f"{'⚠️ ' if dudosa else ''}{e['cargo']} — {e['empresa']}", expanded=dudosa):
            logros = st.text_area("Logros (uno por línea)", "\n".join(e["logros"]), key=f"{k}_e{i}")
            experiencia.append({**e, "logros": [l.strip() for l in logros.splitlines() if l.strip()]})
    habilidades = st.text_area(("⚠️ " if "habilidades" in dudosas else "") + "Habilidades (una por línea)",
                               "\n".join(cv["habilidades"]), key=f"{k}_h")
    return {
        **cv, "nombre": nombre, "titular": titular, "contacto": contacto, "resumen": resumen,
        "experiencia": experiencia,
        "habilidades": [h.strip() for h in habilidades.splitlines() if h.strip()],
    }


def seccion_generar_cv(correo):
    st.header("Generar CV")
    st.caption("graph.generarBorradorCV + graph.generarDocumentoCV")

    if "cv_borrador" not in st.session_state:
        if st.button("Generar CV", type="primary"):
            with st.spinner("El agente está redactando tu CV..."):
                r = llamar(graph.generarBorradorCV, correo)
            if es_contrato(r) and r[0]:
                st.session_state["cv_borrador"] = r[1]
                st.session_state["cv_version"] = st.session_state.get("cv_version", 0) + 1
                st.rerun()
            mostrar_resultado(r)
        return

    cv = st.session_state["cv_borrador"]
    if cv.get("secciones_dudosas"):
        st.warning("Revisa estas secciones: " + ", ".join(cv["secciones_dudosas"]))
    editado = _editor_cv(cv, st.session_state.get("cv_version", 0))

    c1, c2, c3 = st.columns(3)
    if c1.button("✅ Confirmar", type="primary", use_container_width=True):
        st.session_state["cv_doc"] = llamar(graph.generarDocumentoCV, editado)
    if c2.button("🔄 Generar de nuevo", use_container_width=True):
        for k in ("cv_borrador", "cv_doc"):
            st.session_state.pop(k, None)
        st.rerun()
    if c3.button("✖ Rechazar", use_container_width=True):
        for k in ("cv_borrador", "cv_doc"):
            st.session_state.pop(k, None)
        st.rerun()

    r = st.session_state.get("cv_doc")
    if r is not None:
        if es_contrato(r) and r[0]:
            st.success("Documento generado.")
            st.download_button(
                "⬇️ Descargar CV", data=r[1], file_name=f"CV {editado['nombre']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        else:
            mostrar_resultado(r)

    with st.expander("CV en crudo"):
        st.json(cv)


# ===========================================================================
# App
# ===========================================================================

SECCIONES = {
    "Datos generales": seccion_datos_generales,
    "Experiencia": seccion_experiencia,
    "Educación": seccion_educacion,
    "Importar perfil (agente)": seccion_importar,
    "Archivo del CV": seccion_archivo,
    "Generar CV (agente)": seccion_generar_cv,
}

st.session_state.setdefault("usuario_logueado", None)
st.session_state.setdefault("modo_perfil", None)

if st.session_state["usuario_logueado"] is None:
    st.info("🧪 Frontend de prueba. Inicia sesión o crea una cuenta (usa tu login.py real).")
    mostrar_pantalla_login()
else:
    correo = st.session_state["usuario_logueado"]
    with st.sidebar:
        st.title("🧪 Pruebas Progent")
        st.caption(f"Sesión: {correo}")
        seccion = st.radio("Sección", list(SECCIONES))
        st.divider()
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.rerun()
    SECCIONES[seccion](correo)
