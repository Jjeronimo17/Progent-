import streamlit as st

from postulaciones import consultarPostulacion, registrarPostulacion
from vacantes import consultarVacante, consultarVacantes


def boton_volver_listado():
    if st.button("← Volver"):
        st.session_state["vacante_seleccionada"] = None
        st.rerun()


def seleccionar_vacante(id_vacante):
    st.session_state["vacante_seleccionada"] = id_vacante


def mostrar_tarjeta_vacante(vacante):
    with st.container(border=True):
        st.subheader(vacante["Cargo"])
        st.write(f"**{vacante['Empresa']}** · {vacante['Ubicacion']}")

        with st.expander("Ver descripción y requisitos"):
            st.markdown("**Descripción**")
            st.write(vacante["Descripcion"])
            st.markdown("**Requisitos**")
            st.write(vacante["Requisitos"])
            st.caption(f"Publicada el {vacante['Fecha_publicacion']:%d/%m/%Y}")

        # on_click guarda la selección antes de volver a dibujar la página,
        # así funciona aunque la vacante se haya cerrado y ya no salga en la lista.
        st.button(
            "Ver detalle",
            key=f"detalle_{vacante['Id_vacante']}",
            on_click=seleccionar_vacante,
            args=(vacante["Id_vacante"],),
        )


def mostrar_listado_vacantes():
    st.title("Vacantes disponibles")

    palabra_clave = st.text_input(
        "Buscar por palabra clave",
        placeholder="Ej.: Python, analista, remoto",
        help="Busca en el cargo y en la descripción. Borra el texto para ver todas.",
    ).strip()

    exito, resultado = consultarVacantes(palabra_clave)

    if not exito:
        st.error(resultado)
        return

    if not resultado:
        if palabra_clave:
            st.info(f"Sin resultados para «{palabra_clave}». Prueba con otra palabra.")
        else:
            st.info("Por ahora no hay vacantes disponibles. Vuelve a revisar más tarde.")
        return

    cantidad = len(resultado)
    if palabra_clave:
        verbo = "vacante coincide" if cantidad == 1 else "vacantes coinciden"
        st.caption(f"{cantidad} {verbo} con «{palabra_clave}»")
    else:
        sustantivo = "vacante disponible" if cantidad == 1 else "vacantes disponibles"
        st.caption(f"{cantidad} {sustantivo}")
    for vacante in resultado:
        mostrar_tarjeta_vacante(vacante)


def postularse(id_vacante):
    # Se ejecuta con on_click, antes de volver a dibujar la página.
    correo = st.session_state["usuario_logueado"]
    exito, mensaje = registrarPostulacion(correo, id_vacante)
    st.session_state["resultado_postulacion"] = (id_vacante, exito, mensaje)


def ir_a_mis_postulaciones():
    # Cambia la opción del menú lateral (key "seccion" en main.py).
    st.session_state["seccion"] = "Mis postulaciones"


def seccion_postulacion(id_vacante, resultado_postulacion):
    if resultado_postulacion and resultado_postulacion[0] == id_vacante:
        _, exito, mensaje = resultado_postulacion
        if exito:
            st.success(mensaje)
            st.caption(
                "Progent guarda tu postulación para que le hagas seguimiento, "
                "pero no la envía al portal de la empresa."
            )
        else:
            st.warning(mensaje)

    exito, postulacion = consultarPostulacion(
        st.session_state["usuario_logueado"], id_vacante
    )
    if not exito:
        st.error(postulacion)
        return

    if postulacion:
        st.info(
            f"Ya te postulaste a esta vacante el "
            f"{postulacion['Fecha_postulacion']:%d/%m/%Y}."
        )
        st.button("Ver en mis postulaciones", on_click=ir_a_mis_postulaciones)
        return

    st.button(
        "Postularme",
        type="primary",
        use_container_width=True,
        on_click=postularse,
        args=(id_vacante,),
    )


def mostrar_detalle_vacante(id_vacante):
    # El resultado de "Postularme" se muestra una sola vez y solo en su vacante.
    resultado_postulacion = st.session_state.pop("resultado_postulacion", None)
    exito, vacante = consultarVacante(id_vacante)

    if not exito:
        st.error(vacante)
        boton_volver_listado()
        return

    if vacante is None:
        st.error("Esta vacante ya no existe.")
        boton_volver_listado()
        return

    if vacante["Estado"] == "Cerrada":
        st.warning(
            f"La vacante «{vacante['Cargo']}» fue cerrada y ya no recibe postulaciones."
        )
        boton_volver_listado()
        return

    st.title(vacante["Cargo"])
    st.write(f"Publicada por **{vacante['Empresa']}**")
    st.caption(
        f"{vacante['Ubicacion']} · Publicada el "
        f"{vacante['Fecha_publicacion']:%d/%m/%Y}"
    )

    st.subheader("Descripción")
    st.write(vacante["Descripcion"])

    st.subheader("Requisitos")
    st.write(vacante["Requisitos"])

    seccion_postulacion(vacante["Id_vacante"], resultado_postulacion)

    boton_volver_listado()


def mostrar_pantalla_vacantes():
    id_vacante = st.session_state.get("vacante_seleccionada")

    if id_vacante is None:
        mostrar_listado_vacantes()
    else:
        mostrar_detalle_vacante(id_vacante)
