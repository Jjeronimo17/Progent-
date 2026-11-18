import unicodedata

import streamlit as st

from documentos import guardarCvGenerado

# graph se importa dentro de cada función, para que la aplicación arranque aunque falte
# la clave de Anthropic (como en las demás pantallas que usan el agente).

TIPO_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def correo_actual():
    return st.session_state["usuario_logueado"]


def nombre_archivo(cv):
    # Sin tildes: el navegador corta el nombre de la descarga en el primer carácter
    # no ASCII y el archivo quedaba sin la extensión .docx.
    nombre = unicodedata.normalize("NFKD", cv["nombre"]).encode("ascii", "ignore").decode()
    return f"CV {nombre}.docx"


def cv_editado(borrador, ronda):
    """El borrador con lo que el usuario escribió en pantalla."""
    estado = st.session_state
    cv = dict(borrador)
    cv["titular"] = estado.get(f"cv_titular_{ronda}", cv["titular"]).strip()
    cv["resumen"] = estado.get(f"cv_resumen_{ronda}", cv["resumen"]).strip()
    cv["experiencia"] = []
    for i, e in enumerate(borrador["experiencia"]):
        texto = estado.get(f"cv_logros_{ronda}_{i}", "\n".join(e["logros"]))
        cv["experiencia"].append(dict(e, logros=[l.strip("•- ").strip() for l in texto.splitlines() if l.strip()]))
    texto = estado.get(f"cv_habilidades_{ronda}", ", ".join(cv["habilidades"]))
    cv["habilidades"] = [h.strip() for h in texto.split(",") if h.strip()]
    return cv


def confirmar(ronda):
    # Solo lo confirmado se guarda (decisión 7): queda como la hoja de vida del perfil.
    from graph import generarDocumentoCV

    generado = st.session_state["cv_generado"]
    cv = cv_editado(generado["cv"], ronda)
    exito, documento = generarDocumentoCV(cv)
    if exito:
        exito, mensaje = guardarCvGenerado(correo_actual(), nombre_archivo(cv), documento)
    else:
        mensaje = documento
    st.session_state["mensaje_generar_cv"] = (exito, mensaje)
    if exito:
        st.session_state.pop("cv_generado")


def rechazar():
    st.session_state.pop("cv_generado", None)
    st.session_state["mensaje_generar_cv"] = (True, "Rechazaste el CV generado: no se guardó nada.")


def aviso_dudosa(dudosas, seccion, texto):
    if seccion in dudosas:
        st.warning(f"Revisa {texto}: el agente no quedó seguro de cómo redactarla.")


def vista_previa(cv):
    contacto = " · ".join(v for v in cv["contacto"].values() if v)
    bloques = [f"### {cv['nombre']}", cv["titular"], f"*{contacto}*", f"**Perfil profesional**\n\n{cv['resumen']}"]
    experiencia = []
    for e in cv["experiencia"]:
        experiencia.append(f"- **{e['cargo']}** — {e['empresa']} ({e['periodo']})")
        experiencia += [f"    - {l}" for l in e["logros"]]
    bloques.append("**Experiencia**\n\n" + "\n".join(experiencia))
    educacion = [f"- **{e['titulo']}** — {e['institucion']} ({e['periodo']})" for e in cv["educacion"]]
    bloques.append("**Educación**\n\n" + "\n".join(educacion))
    bloques.append("**Habilidades**\n\n" + ", ".join(cv["habilidades"]))
    # Una línea en blanco entre bloques para que Markdown no los junte en un párrafo.
    st.markdown("\n\n".join(b for b in bloques if b))


def mostrar_borrador(generado):
    from graph import generarDocumentoCV

    borrador, ronda = generado["cv"], generado["ronda"]
    dudosas = borrador["secciones_dudosas"]
    if dudosas:
        st.warning(
            "Revisa estas secciones: el agente no quedó seguro de cómo redactarlas: "
            + ", ".join(dudosas) + "."
        )
    st.caption("Es un borrador: nada se guarda hasta que lo confirmes. Puedes editar lo que redactó el agente.")

    with st.container(border=True):
        st.markdown(f"**{borrador['nombre']}**")
        st.caption(" · ".join(v for v in borrador["contacto"].values() if v) + " (se cambia en Mi perfil)")
        st.text_input("Titular", value=borrador["titular"], key=f"cv_titular_{ronda}")
        aviso_dudosa(dudosas, "resumen", "el perfil profesional")
        st.text_area("Perfil profesional", value=borrador["resumen"], key=f"cv_resumen_{ronda}")

        st.markdown("**Experiencia**")
        for i, e in enumerate(borrador["experiencia"]):
            st.markdown(f"{e['cargo']} — {e['empresa']}")
            st.caption(e["periodo"])
            aviso_dudosa(dudosas, f"experiencia {i + 1}", "esta experiencia")
            st.text_area("Logros (uno por línea)", value="\n".join(e["logros"]), key=f"cv_logros_{ronda}_{i}")

        st.markdown("**Educación**")
        for e in borrador["educacion"]:
            st.caption(f"{e['titulo']} — {e['institucion']} · {e['periodo']}")

        aviso_dudosa(dudosas, "habilidades", "las habilidades")
        st.text_area("Habilidades (separadas por comas)", value=", ".join(borrador["habilidades"]),
                     key=f"cv_habilidades_{ronda}")

    cv = cv_editado(borrador, ronda)
    with st.expander("Vista previa del CV"):
        vista_previa(cv)

    exito, documento = generarDocumentoCV(cv)
    if not exito:
        st.error(documento)
        return
    st.download_button("Descargar CV (.docx)", data=documento, file_name=nombre_archivo(cv), mime=TIPO_DOCX)

    st.caption("Al confirmarlo, reemplaza la hoja de vida de tu perfil y es la que se usará al postularte.")
    izquierda, derecha = st.columns(2)
    izquierda.button("Confirmar CV", type="primary", use_container_width=True, on_click=confirmar, args=(ronda,))
    derecha.button("Rechazar", use_container_width=True, on_click=rechazar)


def mostrar_generar_cv():
    st.title("Genera tu CV")
    st.write(
        "El agente redacta tu CV a partir de tu perfil. Revísalo y edítalo; cuando lo "
        "confirmes, queda como tu hoja de vida para postularte."
    )

    mensaje = st.session_state.pop("mensaje_generar_cv", None)
    if mensaje:
        exito, texto = mensaje
        (st.success if exito else st.error)(texto)

    if st.button("Generar mi CV", type="primary"):
        from graph import generarBorradorCV

        with st.spinner("El agente está redactando tu CV..."):
            respuesta = generarBorradorCV(correo_actual())
        ronda = st.session_state.get("ronda_cv", 0) + 1
        st.session_state["ronda_cv"] = ronda
        exito, datos = respuesta
        if exito and datos["cv"]:
            st.session_state["cv_generado"] = {"cv": datos["cv"], "ronda": ronda}
        else:
            st.session_state.pop("cv_generado", None)
            st.session_state["resultado_generar_cv"] = respuesta

    generado = st.session_state.get("cv_generado")
    if generado:
        mostrar_borrador(generado)
        return

    respuesta = st.session_state.pop("resultado_generar_cv", None)
    if respuesta is None:
        return
    exito, datos = respuesta
    if not exito:
        st.error(datos)
        return
    lineas = "\n".join(f"- {f}" for f in datos["faltantes"])
    st.warning(
        "Antes de generar tu CV completa estas secciones de tu perfil:\n"
        f"{lineas}\n\nHazlo en **Mi perfil → Llenar mi perfil manualmente**."
    )
