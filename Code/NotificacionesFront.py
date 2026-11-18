import streamlit as st

from alertas import consultarAlerta, consultarNotificaciones, eliminarAlerta, marcarLeidas

MODALIDADES = {"Hibrido": "Híbrido", "Presencial": "Presencial", "Virtual": "Virtual"}


def describir_alerta(palabra_clave, ubicacion, salario_minimo, modalidad):
    """Ej.: «python» · Medellín · desde $3.000.000 · Híbrido"""
    partes = []
    if palabra_clave:
        partes.append(f"«{palabra_clave}»")
    if ubicacion:
        partes.append(ubicacion)
    if salario_minimo:
        partes.append(f"desde ${int(salario_minimo):,.0f}".replace(",", "."))
    if modalidad:
        partes.append(MODALIDADES.get(modalidad, modalidad))
    return " · ".join(partes)


def correo_actual():
    return st.session_state["usuario_logueado"]


def ver_vacante(id_notificacion, id_vacante):
    # Marca la notificación como leída y lleva al detalle (key "seccion" en main.py).
    marcarLeidas(correo_actual(), id_notificacion)
    st.session_state["seccion"] = "Vacantes"
    st.session_state["vacante_seleccionada"] = id_vacante


def marcar_todas():
    exito, mensaje = marcarLeidas(correo_actual())
    st.session_state["mensaje_notificaciones"] = (exito, mensaje)


def desactivar_alerta():
    exito, mensaje = eliminarAlerta(correo_actual())
    st.session_state["mensaje_notificaciones"] = (exito, mensaje)


def seccion_alerta():
    st.divider()
    st.subheader("Tu alerta")
    exito, alerta = consultarAlerta(correo_actual())
    if not exito:
        st.error(alerta)
        return
    if not alerta:
        st.caption(
            "No tienes una alerta activa. Créala en **Vacantes** con los filtros que "
            "quieras y el botón «Crear alerta con estos filtros»."
        )
        return
    descripcion = describir_alerta(
        alerta["Palabra_clave"], alerta["Ubicacion"], alerta["Salario_minimo"], alerta["Modalidad"]
    )
    st.write(f"Te avisamos de vacantes nuevas: **{descripcion}**")
    st.caption(f"Activa desde el {alerta['Fecha_creacion']:%d/%m/%Y}")
    st.button("Desactivar alerta", on_click=desactivar_alerta)


def mostrar_pantalla_notificaciones():
    st.title("Notificaciones")

    mensaje = st.session_state.pop("mensaje_notificaciones", None)
    if mensaje:
        exito, texto = mensaje
        (st.success if exito else st.error)(texto)

    exito, notificaciones = consultarNotificaciones(correo_actual())
    if not exito:
        st.error(notificaciones)
    elif not notificaciones:
        st.info(
            "No tienes notificaciones. Cuando se publique una vacante que cumpla tu alerta, "
            "aparecerá aquí."
        )
    else:
        if any(not n["Leida"] for n in notificaciones):
            st.button("Marcar todas como leídas", on_click=marcar_todas)
        for notificacion in notificaciones:
            with st.container(border=True):
                nueva = "" if notificacion["Leida"] else "**Nueva** · "
                st.subheader(f"{notificacion['Cargo']}")
                st.write(f"{nueva}**{notificacion['Empresa']}** · {notificacion['Ubicacion']}")
                st.caption(
                    f"Publicada el {notificacion['Fecha_publicacion']:%d/%m/%Y} · "
                    f"te avisamos el {notificacion['Fecha_notificacion']:%d/%m/%Y}"
                )
                cerrada = notificacion["Estado"] == "Cerrada"
                if cerrada:
                    st.warning("Esta vacante ya fue cerrada y no recibe postulaciones.")
                st.button(
                    "Ver detalle",
                    key=f"notificacion_{notificacion['Id_notificacion']}",
                    disabled=cerrada,
                    on_click=ver_vacante,
                    args=(notificacion["Id_notificacion"], notificacion["Id_vacante"]),
                )

    seccion_alerta()
