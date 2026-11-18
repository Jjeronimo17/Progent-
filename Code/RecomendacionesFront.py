import streamlit as st

from datosUsuario import consultarArchivo
from guardadas import guardarVacante
from postulaciones import registrarPostulacion
from recomendaciones import (
    consultarCriterios,
    consultarDeInteres,
    generarRecomendaciones,
    guardarCriterios,
    guardarDecision,
    prepararRecomendaciones,
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


def quitar_de_la_lista(id_vacante):
    resultado = st.session_state.get("resultado_recomendaciones")
    if resultado:
        resultado["recomendaciones"] = [
            r for r in resultado["recomendaciones"] if r["vacante"]["Id_vacante"] != id_vacante
        ]


def decidir(id_vacante, decision, motivo):
    # Se ejecuta con on_click, antes de volver a dibujar la página.
    exito, mensaje = guardarDecision(correo_actual(), id_vacante, decision, motivo)
    st.session_state["mensaje_recomendaciones"] = (exito, mensaje)
    if exito:
        quitar_de_la_lista(id_vacante)


def guardar_recomendada(id_vacante):
    # La guardada pasa a Guardadas y ya no se vuelve a recomendar (#25).
    exito, mensaje = guardarVacante(correo_actual(), id_vacante)
    st.session_state["mensaje_recomendaciones"] = (exito, mensaje)
    if exito:
        quitar_de_la_lista(id_vacante)


def ver_para_postularme(id_vacante):
    # Lleva al detalle de la vacante, donde se elige la hoja de vida y se postula.
    st.session_state["seccion"] = "Vacantes"
    st.session_state["vacante_seleccionada"] = id_vacante


def pedir_confirmacion(id_vacante):
    # "Postularme" no postula: abre la confirmación en la tarjeta (#27).
    st.session_state["confirmando_postulacion"] = id_vacante


def cancelar_confirmacion():
    st.session_state.pop("confirmando_postulacion", None)


def confirmar_postulacion(id_vacante, cargo):
    exito, mensaje = registrarPostulacion(correo_actual(), id_vacante)
    if exito:
        mensaje = f"Te postulaste a «{cargo}». La encuentras en Mis postulaciones."
        quitar_de_la_lista(id_vacante)
        cancelar_confirmacion()
    st.session_state["mensaje_recomendaciones"] = (exito, mensaje)


def rechazar_recomendacion(id_vacante, motivo):
    # Rechazar descarta la sugerencia; no se registra ninguna postulación.
    exito, mensaje = guardarDecision(correo_actual(), id_vacante, "Descartada", motivo)
    if exito:
        mensaje = "Rechazaste la recomendación: no se registró ninguna postulación y no te la volveré a recomendar."
        quitar_de_la_lista(id_vacante)
        cancelar_confirmacion()
    st.session_state["mensaje_recomendaciones"] = (exito, mensaje)


def seccion_confirmar_postulacion(vacante, motivo):
    """Confirmar o rechazar la postulación que sugiere el agente. Nada se registra sin confirmar."""
    id_vacante = vacante["Id_vacante"]
    with st.container(border=True):
        st.markdown(f"**¿Confirmas que quieres postularte a «{vacante['Cargo']}» en {vacante['Empresa']}?**")
        exito, cv = consultarArchivo(correo_actual())
        if not exito:
            st.error(cv)
            return
        if cv is None:
            st.warning(
                "Para postularte necesitas tu hoja de vida. Cárgala en el detalle de la vacante "
                "y postúlate desde ahí."
            )
        else:
            # Columnas de archivos_usuarios: Correos_usuarios, nombre_archivo, tipo, archivo_bytes
            st.caption(
                f"Se registrará en tu panel de seguimiento con tu hoja de vida **{cv[1]}**. "
                "Progent no envía la postulación al portal de la empresa."
            )
        confirmar, rechazar, cancelar = st.columns(3)
        if cv is None:
            confirmar.button(
                "Ver detalle para cargarla",
                key=f"detalle_rec_{id_vacante}",
                use_container_width=True,
                on_click=ver_para_postularme,
                args=(id_vacante,),
            )
        else:
            confirmar.button(
                "Confirmar postulación",
                key=f"confirmar_rec_{id_vacante}",
                type="primary",
                use_container_width=True,
                on_click=confirmar_postulacion,
                args=(id_vacante, vacante["Cargo"]),
            )
        rechazar.button(
            "Rechazar",
            key=f"rechazar_rec_{id_vacante}",
            use_container_width=True,
            on_click=rechazar_recomendacion,
            args=(id_vacante, motivo),
        )
        cancelar.button(
            "Cancelar",
            key=f"cancelar_rec_{id_vacante}",
            use_container_width=True,
            on_click=cancelar_confirmacion,
        )


def mostrar_recomendacion(recomendacion):
    vacante = recomendacion["vacante"]
    id_vacante = vacante["Id_vacante"]
    with st.container(border=True):
        st.subheader(vacante["Cargo"])
        st.write(f"**{vacante['Empresa']}** · {vacante['Ubicacion']}")

        if recomendacion["seguro"]:
            st.markdown(f"**Por qué te la recomiendo:** {recomendacion['motivo']}")
            st.caption("Sugerencia del agente: todavía no te has postulado.")
        else:
            st.caption("Menor relevancia")
            st.warning(
                "No estoy seguro de que esta vacante encaje contigo. "
                f"Te la recomiendo porque: {recomendacion['motivo']} "
                "Es solo una sugerencia: no he hecho nada en tu nombre ni te he postulado."
            )

        with st.expander("Ver descripción y requisitos"):
            st.markdown("**Descripción**")
            st.write(vacante["Descripcion"])
            st.markdown("**Requisitos**")
            st.write(vacante["Requisitos"])

        interesa, guardar, postular, descartar = st.columns(4)
        interesa.button(
            "Me interesa",
            key=f"interesa_{id_vacante}",
            type="primary",
            use_container_width=True,
            on_click=decidir,
            args=(id_vacante, "Interesa", recomendacion["motivo"]),
        )
        guardar.button(
            "Guardar",
            key=f"guardar_rec_{id_vacante}",
            use_container_width=True,
            on_click=guardar_recomendada,
            args=(id_vacante,),
        )
        postular.button(
            "Postularme",
            key=f"postular_rec_{id_vacante}",
            use_container_width=True,
            on_click=pedir_confirmacion,
            args=(id_vacante,),
        )
        descartar.button(
            "Descartar",
            key=f"descartar_{id_vacante}",
            use_container_width=True,
            on_click=decidir,
            args=(id_vacante, "Descartada", recomendacion["motivo"]),
        )
        if st.session_state.get("confirmando_postulacion") == id_vacante:
            seccion_confirmar_postulacion(vacante, recomendacion["motivo"])


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
            st.info(
                "No encontré vacantes que coincidan con tu perfil y tus criterios. "
                "Cuando se publiquen vacantes nuevas las revisaré y te las mostraré aquí."
            )
        else:
            st.info(
                "Ya respondiste todas las recomendaciones. Te mostraré otras cuando se "
                "publiquen vacantes nuevas, o usa «Actualizar recomendaciones»."
            )
        return

    st.caption("Estas son sugerencias del agente. Nada se guarda hasta que respondas.")
    # Primero las que el agente ve claras; las dudosas van al final, como de menor relevancia.
    recomendaciones = sorted(resultado["recomendaciones"], key=lambda r: not r["seguro"])
    if not any(r["seguro"] for r in recomendaciones):
        st.info(
            "No encontré coincidencias claras con tu perfil: estas recomendaciones son de "
            "menor relevancia."
        )
    for recomendacion in recomendaciones:
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


def actualizar_recomendaciones(forzar):
    """Pide recomendaciones sin que el usuario las busque (#25).

    El agente se llama solo la primera vez y cuando cambian el perfil o los criterios,
    o aparecen vacantes candidatas nuevas. Si solo salieron candidatas (porque el
    usuario las decidió, guardó o se postuló), se quitan de la lista sin llamarlo.
    """
    exito, preparado = prepararRecomendaciones(correo_actual())
    if not exito:
        st.session_state["resultado_recomendaciones"] = {
            "respuesta": (False, preparado), "recomendaciones": [], "total": 0, "base": None, "candidatas": set()}
        return

    candidatas = {v["Id_vacante"] for v in preparado["candidatas"]}
    anterior = st.session_state.get("resultado_recomendaciones")
    if (
        not forzar
        and anterior is not None
        and anterior["base"] == preparado["base"]
        and candidatas <= anterior["candidatas"]
    ):
        anterior["recomendaciones"] = [
            r for r in anterior["recomendaciones"] if r["vacante"]["Id_vacante"] in candidatas
        ]
        return

    with st.spinner("El agente está actualizando tus recomendaciones..."):
        exito, datos = generarRecomendaciones(correo_actual(), preparado)
    recomendaciones = datos["recomendaciones"] if exito else []
    st.session_state["resultado_recomendaciones"] = {
        "respuesta": (exito, datos),
        "recomendaciones": list(recomendaciones),
        "total": len(recomendaciones),
        "base": preparado["base"],
        "candidatas": candidatas,
    }


def mostrar_pantalla_recomendaciones():
    st.title("Vacantes recomendadas")
    st.caption(
        "El agente revisa tu perfil y tus criterios y te sugiere vacantes sin que tengas que "
        "buscarlas. Se actualizan solas cuando cambias tu perfil o se publican vacantes nuevas."
    )

    mensaje = st.session_state.pop("mensaje_recomendaciones", None)
    if mensaje:
        exito, texto = mensaje
        if exito:
            st.success(texto)
        else:
            st.warning(texto)

    seccion_criterios()

    forzar = st.button("Actualizar recomendaciones")
    actualizar_recomendaciones(forzar)

    seccion_resultado()
    seccion_de_interes()
