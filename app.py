"""Interfaz de la prueba de concepto de Progent.

Ejecutar con:  streamlit run app.py
"""

import json

import streamlit as st

from graph import procesar_cv

st.set_page_config(page_title="Progent - Importar hoja de vida", page_icon="📄")

st.title("Progent")
st.caption("Prueba de concepto: importar una hoja de vida y estructurarla con un agente")

# ---------------------------------------------------------------- ENTRADA
archivo = st.file_uploader("Sube tu hoja de vida en PDF", type=["pdf"])

if archivo and st.button("Extraer datos", type="primary"):
    with st.spinner("El agente esta leyendo la hoja de vida..."):
        st.session_state.resultado = procesar_cv(archivo.getvalue())

# ---------------------------------------------------------------- SALIDA
resultado = st.session_state.get("resultado")

if resultado:
    for e in resultado.get("errores", []):
        st.error(e)

    perfil = resultado.get("perfil")
    if perfil:
        dudosos = perfil.get("campos_dudosos") or []
        if dudosos:
            st.warning("El agente no quedo seguro de: " + ", ".join(dudosos))

        st.subheader("Revisa y corrige lo que este mal")

        col1, col2 = st.columns(2)
        contacto = perfil.get("contacto") or {}
        with col1:
            nombre = st.text_input("Nombre completo", perfil.get("nombre_completo") or "")
            correo = st.text_input("Correo", contacto.get("correo") or "")
        with col2:
            titular = st.text_input("Titular", perfil.get("titular") or "")
            telefono = st.text_input("Telefono", contacto.get("telefono") or "")

        st.markdown("**Experiencia**")
        for i, exp in enumerate(perfil.get("experiencia") or []):
            fin = "Actual" if exp.get("actual") else (exp.get("fecha_fin") or "?")
            with st.expander(f"{exp.get('cargo','(sin cargo)')} - {exp.get('empresa','')}"):
                st.write(f"{exp.get('fecha_inicio') or '?'} a {fin}")
                st.write(exp.get("descripcion") or "_Sin descripcion_")

        st.markdown("**Educacion**")
        for edu in perfil.get("educacion") or []:
            st.write(f"- {edu.get('titulo','')} — {edu.get('institucion','')}")

        habilidades = perfil.get("habilidades") or []
        if habilidades:
            st.markdown("**Habilidades**")
            st.write(", ".join(habilidades))

        if st.button("Confirmar perfil"):
            perfil["nombre_completo"] = nombre
            perfil["titular"] = titular
            perfil.setdefault("contacto", {})["correo"] = correo
            perfil["contacto"]["telefono"] = telefono
            st.session_state.perfil_confirmado = perfil
            st.success("Perfil confirmado y guardado en la sesion.")

        with st.expander("Ver JSON crudo (para la sustentacion)"):
            st.json(perfil)
