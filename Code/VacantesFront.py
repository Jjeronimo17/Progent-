import streamlit as st

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

    exito, resultado = consultarVacantes()

    if not exito:
        st.error(resultado)
        return

    if not resultado:
        st.info("Por ahora no hay vacantes disponibles. Vuelve a revisar más tarde.")
        return

    st.caption(f"{len(resultado)} vacantes disponibles")
    for vacante in resultado:
        mostrar_tarjeta_vacante(vacante)


def mostrar_detalle_vacante(id_vacante):
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

    st.button(
        "Postularme",
        type="primary",
        use_container_width=True,
        disabled=True,
        help="Disponible próximamente.",
    )

    boton_volver_listado()


def mostrar_pantalla_vacantes():
    id_vacante = st.session_state.get("vacante_seleccionada")

    if id_vacante is None:
        mostrar_listado_vacantes()
    else:
        mostrar_detalle_vacante(id_vacante)
