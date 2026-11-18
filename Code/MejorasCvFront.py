import streamlit as st

from mejorasCv import aplicarSugerencia, consultarVacantesInteres, generarSugerencias


def correo_actual():
    return st.session_state["usuario_logueado"]


def titulo_sugerencia(sugerencia, experiencias):
    if sugerencia["campo"] == "ocupacion":
        return "Ocupación (titular de tu perfil)"
    experiencia = experiencias.get(sugerencia["id_experiencia"], "tu experiencia")
    if sugerencia["campo"] == "funciones":
        return f"Funciones de «{experiencia}»"
    return f"Habilidades de «{experiencia}»"


def quitar_sugerencia(numero):
    resultado = st.session_state.get("mejoras_cv")
    if resultado:
        resultado["sugerencias"] = [s for s in resultado["sugerencias"] if s["numero"] != numero]


def aplicar(sugerencia, clave_texto):
    # Se ejecuta con on_click: aplica el texto que se ve en pantalla (el usuario pudo editarlo).
    exito, mensaje = aplicarSugerencia(
        correo_actual(), sugerencia["campo"], sugerencia["id_experiencia"], st.session_state[clave_texto]
    )
    st.session_state["mensaje_mejoras"] = (exito, mensaje)
    if exito:
        quitar_sugerencia(sugerencia["numero"])


def descartar(numero):
    quitar_sugerencia(numero)
    st.session_state["mensaje_mejoras"] = (True, "Descartaste la sugerencia; tu perfil no cambió.")


def mostrar_sugerencia(sugerencia, experiencias, ronda):
    numero = sugerencia["numero"]
    with st.container(border=True):
        st.markdown(f"**{titulo_sugerencia(sugerencia, experiencias)}**")
        if sugerencia["seguro"]:
            st.caption("Cambio sugerido")
            st.markdown(f"**Por qué:** {sugerencia['motivo']}")
        else:
            st.warning(
                "Recomendación: no estoy seguro de este cambio. "
                f"{sugerencia['motivo']} Aplícalo solo si es cierto; no se cambia nada por sí solo."
            )
        if sugerencia["vacantes"]:
            st.caption("Según: " + ", ".join(sugerencia["vacantes"]))
        if sugerencia["campo"] != "habilidades" and sugerencia["actual"]:
            st.caption(f"Ahora dice: {sugerencia['actual']}")
        elif sugerencia["campo"] == "habilidades":
            st.caption(f"Habilidades actuales: {sugerencia['actual'] or 'ninguna'}")

        clave_texto = f"mejora_texto_{ronda}_{numero}"
        etiqueta = "Habilidades para agregar" if sugerencia["campo"] == "habilidades" else "Texto propuesto"
        if sugerencia["campo"] == "habilidades":
            st.text_input(etiqueta, value=sugerencia["propuesta"], key=clave_texto)
        else:
            st.text_area(etiqueta, value=sugerencia["propuesta"], key=clave_texto)

        izquierda, derecha = st.columns(2)
        izquierda.button(
            "Aplicar a mi perfil",
            key=f"aplicar_mejora_{ronda}_{numero}",
            type="primary",
            use_container_width=True,
            on_click=aplicar,
            args=(sugerencia, clave_texto),
        )
        derecha.button(
            "Descartar",
            key=f"descartar_mejora_{ronda}_{numero}",
            use_container_width=True,
            on_click=descartar,
            args=(numero,),
        )


def seccion_resultado():
    resultado = st.session_state.get("mejoras_cv")
    if resultado is None:
        return

    exito, datos = resultado["respuesta"]
    if not exito:
        st.error(datos)
        return

    if datos["faltantes"]:
        lineas = "\n".join(f"- {f}" for f in datos["faltantes"])
        st.warning(
            "Para sugerirte mejoras necesito que completes tu perfil. Te falta:\n"
            f"{lineas}\n\nComplétalo en **Mi perfil → Llenar mi perfil manualmente**."
        )
        return

    if datos["sin_interes"]:
        st.warning(
            "Para sugerirte mejoras necesito saber qué vacantes te interesan. Guarda al menos "
            "una con **Guardar vacante** en su detalle (o márcala con **Me interesa** en "
            "Recomendaciones) y vuelve a pedir sugerencias."
        )
        return

    if datos["errores"]:
        st.error(" ".join(datos["errores"]))
        return

    if not resultado["sugerencias"]:
        if resultado["total"] == 0:
            st.info("Tu perfil ya encaja con tus vacantes de interés: el agente no encontró cambios para sugerirte.")
        else:
            st.info("Ya revisaste todas las sugerencias.")
        return

    st.caption("Son sugerencias del agente: tu perfil solo cambia cuando aplicas una.")
    for sugerencia in resultado["sugerencias"]:
        mostrar_sugerencia(sugerencia, datos["experiencias"], resultado["ronda"])


def mostrar_mejorar_cv():
    st.title("Mejora tu hoja de vida")
    st.write(
        "El agente compara tu perfil con las vacantes que te interesan y te sugiere "
        "cambios concretos. Puedes aplicar o descartar cada uno."
    )

    mensaje = st.session_state.pop("mensaje_mejoras", None)
    if mensaje:
        exito, texto = mensaje
        (st.success if exito else st.error)(texto)

    exito, vacantes = consultarVacantesInteres(correo_actual())
    if not exito:
        st.error(vacantes)
    elif vacantes:
        st.caption("Se comparará con: " + "; ".join(f"{v['Cargo']} ({v['Empresa']})" for v in vacantes))

    if st.button("Pedir sugerencias", type="primary"):
        with st.spinner("El agente está comparando tu perfil con tus vacantes de interés..."):
            exito, datos = generarSugerencias(correo_actual())
        sugerencias = datos["sugerencias"] if exito else []
        ronda = st.session_state.get("mejoras_cv", {}).get("ronda", 0) + 1
        st.session_state["mejoras_cv"] = {
            "respuesta": (exito, datos),
            "sugerencias": [dict(s, numero=i) for i, s in enumerate(sugerencias)],
            "total": len(sugerencias),
            "ronda": ronda,
        }

    seccion_resultado()
