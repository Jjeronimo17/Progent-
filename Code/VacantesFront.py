import streamlit as st

from alertas import guardarAlerta
from CompatibilidadFront import seccion_compatibilidad
from datosUsuario import consultarArchivo
from documentos import guardarCvPerfil
from guardadas import estaGuardada, guardarVacante, quitarVacanteGuardada
from NotificacionesFront import describir_alerta
from PostulacionesFront import seccion_carta
from postulaciones import consultarPostulacion, registrarPostulacion
from vacantes import consultarUbicaciones, consultarVacante, consultarVacantes

MODALIDADES = {"Hibrido": "Híbrido", "Presencial": "Presencial", "Virtual": "Virtual"}


def boton_volver_listado():
    if st.button("← Volver"):
        st.session_state["vacante_seleccionada"] = None
        st.rerun()


def texto_salario_modalidad(vacante):
    """Ej.: "$6.500.000 al mes · Híbrido". Los nombres de la base van sin tilde."""
    if vacante["Salario"] is None:
        salario = "Salario no publicado"
    else:
        salario = f"${vacante['Salario']:,.0f} al mes".replace(",", ".")
    modalidad = MODALIDADES.get(vacante["Modalidad"], "Modalidad no indicada")
    return f"{salario} · {modalidad}"


def seleccionar_vacante(id_vacante):
    st.session_state["vacante_seleccionada"] = id_vacante


def mostrar_tarjeta_vacante(vacante):
    with st.container(border=True):
        st.subheader(vacante["Cargo"])
        st.write(f"**{vacante['Empresa']}** · {vacante['Ubicacion']}")
        st.caption(texto_salario_modalidad(vacante))

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


def mostrar_filtros():
    """Dibuja los filtros y devuelve (ubicación, salario mínimo, modalidad); None = sin filtro."""
    exito, ubicaciones = consultarUbicaciones()
    if not exito:
        st.error(ubicaciones)
        ubicaciones = []

    columna1, columna2, columna3 = st.columns(3)
    ubicacion = columna1.selectbox("Ubicación", ["Todas"] + ubicaciones, key="filtro_ubicacion")
    salario_minimo = columna2.number_input(
        "Salario mínimo (COP al mes)",
        min_value=0,
        step=500000,
        value=None,
        placeholder="Sin mínimo",
        key="filtro_salario",
    )
    modalidad = columna3.selectbox(
        "Modalidad",
        ["Todas"] + list(MODALIDADES),
        format_func=lambda m: MODALIDADES.get(m, m),
        key="filtro_modalidad",
    )
    return (
        None if ubicacion == "Todas" else ubicacion,
        salario_minimo or None,
        None if modalidad == "Todas" else modalidad,
    )


def crear_alerta(palabra_clave, ubicacion, salario_minimo, modalidad):
    # Se ejecuta con on_click: guarda la alerta con los filtros que se ven en pantalla.
    exito, mensaje = guardarAlerta(
        st.session_state["usuario_logueado"], palabra_clave, ubicacion, salario_minimo, modalidad
    )
    if exito:
        criterios = describir_alerta(palabra_clave, ubicacion, salario_minimo, modalidad)
        mensaje = f"{mensaje} Criterios: {criterios}."
    st.session_state["mensaje_alerta"] = (exito, mensaje)


def boton_crear_alerta(palabra_clave, ubicacion, salario_minimo, modalidad):
    mensaje = st.session_state.pop("mensaje_alerta", None)
    if mensaje:
        exito, texto = mensaje
        (st.success if exito else st.error)(texto)
    hay_criterios = bool(palabra_clave or ubicacion or salario_minimo or modalidad)
    st.button(
        "Crear alerta con estos filtros",
        disabled=not hay_criterios,
        help="Te avisaremos en Notificaciones cuando se publique una vacante nueva que "
        "cumpla la búsqueda y los filtros actuales."
        if hay_criterios
        else "Escribe una palabra clave o elige al menos un filtro.",
        on_click=crear_alerta,
        args=(palabra_clave, ubicacion, salario_minimo, modalidad),
    )


def mostrar_listado_vacantes():
    st.title("Vacantes disponibles")

    palabra_clave = st.text_input(
        "Buscar por palabra clave",
        placeholder="Ej.: Python, analista, remoto",
        help="Busca en el cargo y en la descripción. Borra el texto para ver todas.",
    ).strip()

    ubicacion, salario_minimo, modalidad = mostrar_filtros()
    hay_filtros = bool(ubicacion or salario_minimo or modalidad)
    boton_crear_alerta(palabra_clave, ubicacion, salario_minimo, modalidad)

    exito, resultado = consultarVacantes(palabra_clave, ubicacion, salario_minimo, modalidad)

    if not exito:
        st.error(resultado)
        return

    if not resultado:
        if hay_filtros:
            con_palabra = f" con «{palabra_clave}»" if palabra_clave else ""
            st.info(
                f"Sin resultados: ninguna vacante{con_palabra} cumple los filtros "
                "seleccionados. Prueba quitando alguno."
            )
        elif palabra_clave:
            st.info(f"Sin resultados para «{palabra_clave}». Prueba con otra palabra.")
        else:
            st.info("Por ahora no hay vacantes disponibles. Vuelve a revisar más tarde.")
        return

    cantidad = len(resultado)
    if hay_filtros:
        verbo = "vacante cumple" if cantidad == 1 else "vacantes cumplen"
        coincide = "coincide" if cantidad == 1 else "coinciden"
        con_palabra = f" y {coincide} con «{palabra_clave}»" if palabra_clave else ""
        st.caption(f"{cantidad} {verbo} los filtros{con_palabra}")
    elif palabra_clave:
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
        if postulacion["Cv"]:
            st.write(f"Hoja de vida asociada a esta postulación: **{postulacion['Cv']}**")
        else:
            st.caption("Esta postulación no tiene hoja de vida asociada.")
        st.button("Ver en mis postulaciones", on_click=ir_a_mis_postulaciones)
        st.markdown("**Carta de presentación** (opcional)")
        seccion_carta(postulacion["Id_postulacion"])
        return

    seccion_hoja_de_vida(id_vacante)


def seccion_hoja_de_vida(id_vacante):
    """Antes de postularse: elegir la hoja de vida guardada o cargarla si no hay (#20)."""
    correo = st.session_state["usuario_logueado"]
    mensaje = st.session_state.pop("mensaje_cv", None)
    if mensaje:
        exito, texto = mensaje
        (st.success if exito else st.error)(texto)

    exito, cv = consultarArchivo(correo)
    if not exito:
        st.error(cv)
        return

    if cv is None:
        st.info(
            "Para postularte necesitas tu hoja de vida. Cárgala aquí: quedará guardada "
            "en tu perfil para tus próximas postulaciones."
        )
        numero = st.session_state.get("cargas_cv", 0)
        archivo = st.file_uploader("Tu hoja de vida (PDF o Word, máx. 5 MB)", key=f"cv_{numero}")
        if st.button("Guardar hoja de vida", disabled=archivo is None):
            exito, texto = guardarCvPerfil(correo, archivo.name, archivo.getvalue())
            st.session_state["mensaje_cv"] = (exito, texto)
            if exito:
                st.session_state["cargas_cv"] = numero + 1
            st.rerun()
    else:
        # Columnas de archivos_usuarios: Correos_usuarios, nombre_archivo, tipo, archivo_bytes
        st.radio(
            "Hoja de vida para esta postulación",
            [cv[1]],
            format_func=lambda nombre: f"{nombre} (guardada en tu perfil)",
            key=f"cv_elegido_{id_vacante}",
        )
    # "Postularme" siempre se ve (#10); sin hoja de vida, el intento pide cargarla (#20).
    st.button(
        "Postularme",
        type="primary",
        use_container_width=True,
        on_click=postularse,
        args=(id_vacante,),
    )


def cambiar_guardada(id_vacante, guardada):
    # Se ejecuta con on_click: guarda o quita la vacante antes de volver a dibujar.
    correo = st.session_state["usuario_logueado"]
    if guardada:
        exito, mensaje = quitarVacanteGuardada(correo, id_vacante)
    else:
        exito, mensaje = guardarVacante(correo, id_vacante)
    st.session_state["resultado_guardar"] = (id_vacante, exito, mensaje)


def seccion_guardar(id_vacante, resultado_guardar):
    if resultado_guardar and resultado_guardar[0] == id_vacante:
        _, exito, mensaje = resultado_guardar
        (st.success if exito else st.error)(mensaje)

    exito, guardada = estaGuardada(st.session_state["usuario_logueado"], id_vacante)
    if not exito:
        st.error(guardada)
        return
    st.button(
        "Quitar de guardadas" if guardada else "Guardar vacante",
        key=f"guardar_{id_vacante}",
        on_click=cambiar_guardada,
        args=(id_vacante, guardada),
    )


def mostrar_detalle_vacante(id_vacante):
    # El resultado de "Postularme" se muestra una sola vez y solo en su vacante.
    resultado_postulacion = st.session_state.pop("resultado_postulacion", None)
    resultado_guardar = st.session_state.pop("resultado_guardar", None)
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
    st.write(texto_salario_modalidad(vacante))
    seccion_guardar(vacante["Id_vacante"], resultado_guardar)

    st.subheader("Descripción")
    st.write(vacante["Descripcion"])

    st.subheader("Requisitos")
    st.write(vacante["Requisitos"])

    seccion_compatibilidad(vacante["Id_vacante"])

    seccion_postulacion(vacante["Id_vacante"], resultado_postulacion)

    boton_volver_listado()


def mostrar_pantalla_vacantes():
    id_vacante = st.session_state.get("vacante_seleccionada")

    if id_vacante is None:
        mostrar_listado_vacantes()
    else:
        mostrar_detalle_vacante(id_vacante)
