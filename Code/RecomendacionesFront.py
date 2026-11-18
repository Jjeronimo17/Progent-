import streamlit as st

from recomendaciones import (
    consultarCriterios,
    consultarDeInteres,
    generarRecomendaciones,
    guardarCriterios,
    guardarDecision,
)

MODALIDADES = ["Cualquiera", "Hibrido", "Presencial", "Virtual"]


def correo_actual():
    return st.session_state["usuario_logueado"]


def seccion_criterios():
    exito, criterios = consultarCriterios(correo_actual())
    if not exito:
        st.error(criterios)
    criterios = criterios if exito and criterios else {}

    with st.expander("Mis criterios de búsqueda", expanded=not criterios):
        with st.form("form_criterios"):
            cargo = st.text_input(
                "Cargo que buscas",
                value=criterios.get("Cargo_deseado") or "",
                max_chars=150,
                placeholder="Ej.: Desarrollador backend",
            )
            modalidad_actual = criterios.get("Modalidad") or "Cualquiera"
            modalidad = st.selectbox(
                "Modalidad", MODALIDADES, index=MODALIDADES.index(modalidad_actual)
            )
            ciudad = st.text_input(
                "Ciudad",
                value=criterios.get("Ciudad") or "",
                max_chars=100,
                help="Solo se usa para filtrar vacantes (también se incluyen las remotas). "
                "No se envía al agente.",
            )
            guardar = st.form_submit_button("Guardar criterios")

        if guardar:
            exito, mensaje = guardarCriterios(
                correo_actual(),
                cargo.strip() or None,
                None if modalidad == "Cualquiera" else modalidad,
                ciudad.strip() or None,
            )
            if exito:
                # Las recomendaciones mostradas eran para los criterios anteriores.
                st.session_state.pop("resultado_recomendaciones", None)
                st.session_state["mensaje_recomendaciones"] = (True, mensaje)
                st.rerun()
            else:
                st.error(mensaje)


def decidir(id_vacante, decision, motivo):
    # Se ejecuta con on_click, antes de volver a dibujar la página.
    exito, mensaje = guardarDecision(correo_actual(), id_vacante, decision, motivo)
    st.session_state["mensaje_recomendaciones"] = (exito, mensaje)
    if exito:
        resultado = st.session_state.get("resultado_recomendaciones")
        if resultado:
            resultado["recomendaciones"] = [
                r for r in resultado["recomendaciones"] if r["vacante"]["Id_vacante"] != id_vacante
            ]


def mostrar_recomendacion(recomendacion):
    vacante = recomendacion["vacante"]
    id_vacante = vacante["Id_vacante"]
    with st.container(border=True):
        st.subheader(vacante["Cargo"])
        st.write(f"**{vacante['Empresa']}** · {vacante['Ubicacion']}")

        if recomendacion["seguro"]:
            st.markdown(f"**Por qué te la recomiendo:** {recomendacion['motivo']}")
        else:
            st.warning(
                "No estoy seguro de que esta vacante encaje contigo. "
                f"Te la recomiendo porque: {recomendacion['motivo']}"
            )

        with st.expander("Ver descripción y requisitos"):
            st.markdown("**Descripción**")
            st.write(vacante["Descripcion"])
            st.markdown("**Requisitos**")
            st.write(vacante["Requisitos"])

        izquierda, derecha = st.columns(2)
        izquierda.button(
            "Me interesa",
            key=f"interesa_{id_vacante}",
            type="primary",
            use_container_width=True,
            on_click=decidir,
            args=(id_vacante, "Interesa", recomendacion["motivo"]),
        )
        derecha.button(
            "Descartar",
            key=f"descartar_{id_vacante}",
            use_container_width=True,
            on_click=decidir,
            args=(id_vacante, "Descartada", recomendacion["motivo"]),
        )


def seccion_resultado():
    resultado = st.session_state.get("resultado_recomendaciones")
    if resultado is None:
        return

    exito, datos = resultado["respuesta"]
    if not exito:
        st.error(datos)
        return

    if datos["faltantes"]:
        lineas = "\n".join(f"- {f}" for f in datos["faltantes"])
        st.warning(
            "Para recomendarte vacantes necesito que completes tu perfil. Te falta:\n"
            f"{lineas}\n\nComplétalo en **Mi perfil → Llenar mi perfil manualmente**."
        )
        return

    if datos["sin_candidatas"]:
        st.info(
            "No hay vacantes nuevas para recomendarte con tus criterios. "
            "Prueba cambiando la ciudad o vuelve más tarde."
        )
        return

    if datos["errores"]:
        st.error(" ".join(datos["errores"]))
        return

    if not resultado["recomendaciones"]:
        if resultado["total"] == 0:
            st.info("El agente no encontró vacantes que encajen con tu perfil y tus criterios.")
        else:
            st.info("Ya respondiste todas las recomendaciones. Busca de nuevo para ver otras.")
        return

    st.caption("Estas son sugerencias del agente. Nada se guarda hasta que respondas.")
    for recomendacion in resultado["recomendaciones"]:
        mostrar_recomendacion(recomendacion)


def seccion_de_interes():
    exito, vacantes = consultarDeInteres(correo_actual())
    if not exito:
        st.error(vacantes)
        return
    if not vacantes:
        return

    st.divider()
    st.subheader("Vacantes que marcaste de interés")
    for vacante in vacantes:
        cerrada = " (cerrada)" if vacante["Estado"] == "Cerrada" else ""
        st.write(f"- **{vacante['Cargo']}** en {vacante['Empresa']}{cerrada}")


def mostrar_pantalla_recomendaciones():
    st.title("Vacantes recomendadas")

    mensaje = st.session_state.pop("mensaje_recomendaciones", None)
    if mensaje:
        exito, texto = mensaje
        if exito:
            st.success(texto)
        else:
            st.warning(texto)

    seccion_criterios()

    if st.button("Buscar recomendaciones", type="primary"):
        with st.spinner("El agente está revisando tu perfil y las vacantes..."):
            exito, datos = generarRecomendaciones(correo_actual())
        recomendaciones = datos["recomendaciones"] if exito else []
        st.session_state["resultado_recomendaciones"] = {
            "respuesta": (exito, datos),
            "recomendaciones": list(recomendaciones),
            "total": len(recomendaciones),
        }

    seccion_resultado()
    seccion_de_interes()
