import streamlit as st

from compatibilidad import calcularCompatibilidad

ICONOS = {"si": "✅ Cumple", "parcial": "🟡 Cumple en parte", "no": "❌ No cumple"}


def mostrar_resultado(datos):
    if datos["perfil_vacio"]:
        st.warning(
            "Tu perfil no tiene información para compararlo con esta vacante. Agrega tu "
            "ocupación, experiencia o educación en **Mi perfil → Llenar mi perfil manualmente**."
        )
        return
    if datos["errores"]:
        st.error(" ".join(datos["errores"]))
        return

    if datos["insuficiente"]:
        falta = f" (te falta: {', '.join(datos['falta'])})" if datos["falta"] else ""
        st.warning(
            f"Tu perfil no tiene suficiente información{falta}: el resultado puede no ser "
            "preciso. Complétalo en Mi perfil para una comparación mejor."
        )

    aproximada = " · aproximada" if datos["aproximado"] else ""
    st.markdown(f"**Compatibilidad: {datos['nivel']} ({datos['porcentaje']} %){aproximada}**")
    st.caption(
        f"Calculada con {len(datos['criterios'])} requisitos de la vacante: cumple = 1, "
        "en parte = ½ y no cumple = 0. Alta desde 70 %, media desde 40 %."
    )
    for criterio in datos["criterios"]:
        aproximado = " · *aproximado: el agente no quedó seguro*" if not criterio["seguro"] else ""
        st.markdown(f"{ICONOS[criterio['cumple']]} — **{criterio['requisito']}**{aproximado}")
        if criterio["dato_perfil"]:
            st.caption(f"Me basé en: {criterio['dato_perfil']}")
        else:
            st.caption("Tu perfil no lo menciona.")
    st.caption("Es una estimación del agente para ayudarte a decidir; no se guarda ni se envía a la empresa.")


def seccion_compatibilidad(id_vacante):
    """Nivel de compatibilidad del perfil con la vacante, antes de postularse (#26)."""
    clave = f"compatibilidad_{id_vacante}"
    with st.expander("Mi compatibilidad con esta vacante", expanded=clave in st.session_state):
        st.caption("El agente compara cada requisito de la vacante con tu perfil.")
        if st.button("Calcular mi compatibilidad", key=f"calcular_{clave}"):
            with st.spinner("El agente está comparando tu perfil con la vacante..."):
                st.session_state[clave] = calcularCompatibilidad(st.session_state["usuario_logueado"], id_vacante)
        respuesta = st.session_state.get(clave)
        if respuesta is None:
            return
        exito, datos = respuesta
        if not exito:
            st.error(datos)
            return
        mostrar_resultado(datos)
