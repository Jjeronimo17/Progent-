import streamlit as st

from guardadas import consultarGuardadas, quitarVacanteGuardada


def ver_detalle_guardada(id_vacante):
    # Lleva al detalle de la vacante (menú "Vacantes", key "seccion" en main.py).
    st.session_state["seccion"] = "Vacantes"
    st.session_state["vacante_seleccionada"] = id_vacante


def quitar_guardada(id_vacante):
    exito, mensaje = quitarVacanteGuardada(st.session_state["usuario_logueado"], id_vacante)
    st.session_state["mensaje_guardadas"] = (exito, mensaje)


def mostrar_pantalla_guardadas():
    st.title("Vacantes guardadas")

    mensaje = st.session_state.pop("mensaje_guardadas", None)
    if mensaje:
        exito, texto = mensaje
        if exito:
            st.success(texto)
        else:
            st.error(texto)

    exito, guardadas = consultarGuardadas(st.session_state["usuario_logueado"])
    if not exito:
        st.error(guardadas)
        return

    if not guardadas:
        st.info(
            "Todavía no has guardado vacantes. Usa **Guardar vacante** en el detalle "
            "de cualquier vacante para revisarla después."
        )
        return

    for vacante in guardadas:
        id_vacante = vacante["Id_vacante"]
        with st.container(border=True):
            st.subheader(vacante["Cargo"])
            st.write(f"**{vacante['Empresa']}** · {vacante['Ubicacion']}")
            st.caption(f"La guardaste el {vacante['Fecha_guardada']:%d/%m/%Y}")
            if vacante["Estado"] == "Cerrada":
                st.warning("Esta vacante ya fue cerrada y no recibe postulaciones.")

            izquierda, derecha = st.columns(2)
            izquierda.button(
                "Ver detalle",
                key=f"ver_guardada_{id_vacante}",
                use_container_width=True,
                disabled=vacante["Estado"] == "Cerrada",
                on_click=ver_detalle_guardada,
                args=(id_vacante,),
            )
            derecha.button(
                "Quitar",
                key=f"quitar_guardada_{id_vacante}",
                use_container_width=True,
                on_click=quitar_guardada,
                args=(id_vacante,),
            )
