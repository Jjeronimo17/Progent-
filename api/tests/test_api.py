"""Pruebas de la API: sesión, dueño de los datos, archivos, decisión 7 y flujos principales."""
from urllib.parse import unquote

from fastapi.testclient import TestClient

import main
from conftest import (
    archivo, cv_guardado, id_vacante_abierta, modo, nuevo_usuario, perfil_completo, sql,
)


# ---------------------------------------------------------------- sesión
def test_sin_sesion_responde_401():
    r = TestClient(main.app).get("/api/perfil")
    assert r.status_code == 401
    assert r.json() == {"ok": False, "mensaje": "Inicia sesión para continuar.", "datos": None}


def test_token_falso_responde_401():
    cliente = TestClient(main.app)
    cliente.cookies.set("progent_sesion", "no.es.un.token")
    assert cliente.get("/api/perfil").status_code == 401


def test_registro_valida_como_la_pantalla():
    c = TestClient(main.app)
    assert c.post("/api/auth/registro", json={"correo": "", "contrasena": ""}).json()["mensaje"] == \
        "Completa el correo y la contraseña."
    assert c.post("/api/auth/registro", json={"correo": "sin-arroba", "contrasena": "clave1234"}).json()["mensaje"] == \
        "Escribe un correo válido."
    assert c.post("/api/auth/registro", json={"correo": "a@b.co", "contrasena": "corta"}).json()["mensaje"] == \
        "La contraseña debe tener al menos 8 caracteres."


def test_correo_repetido():
    c, correo = nuevo_usuario(entrar=False)
    r = c.post("/api/auth/registro", json={"correo": correo, "contrasena": "clave1234"}).json()
    assert r == {"ok": False, "mensaje": "Correo asociado a una cuenta, use otro", "datos": None}


def test_login_correo_sin_cuenta_no_tumba_la_api():
    r = TestClient(main.app).post("/api/auth/login", json={"correo": "nadie@ejemplo.com", "contrasena": "clave1234"})
    assert r.status_code == 200
    assert r.json()["mensaje"] == "Correo o contraseña incorrectos."


def test_login_clave_incorrecta_y_mayusculas():
    c, correo = nuevo_usuario(entrar=False)
    assert c.post("/api/auth/login", json={"correo": correo, "contrasena": "otra12345"}).json()["ok"] is False
    assert c.post("/api/auth/login", json={"correo": correo.upper(), "contrasena": "clave1234"}).json()["ok"] is True
    assert c.get("/api/auth/sesion").json()["datos"]["correo"] == correo


def test_logout_cierra_la_sesion():
    c, _ = nuevo_usuario()
    c.post("/api/auth/logout")
    assert c.get("/api/auth/sesion").status_code == 401


# ---------------------------------------------------------------- dueño de los datos
def test_otro_usuario_no_toca_mi_postulacion():
    yo, mi_correo = nuevo_usuario()
    perfil_completo(mi_correo)
    cv_guardado(mi_correo)
    id_vacante = id_vacante_abierta()
    assert yo.post(f"/api/vacantes/{id_vacante}/postular").json()["ok"]
    id_postulacion = yo.get("/api/postulaciones").json()["datos"][0]["Id_postulacion"]

    otro, _ = nuevo_usuario()
    assert otro.get("/api/postulaciones").json()["datos"] == []
    r = otro.put(f"/api/postulaciones/{id_postulacion}/estado", json={"estado": "En revisión"}).json()
    assert r["ok"] is False
    r = otro.put(f"/api/postulaciones/{id_postulacion}/carta",
                 files={"archivo": ("carta.pdf", archivo("carta.pdf"), "application/pdf")}).json()
    assert r == {"ok": False, "mensaje": "Esta postulación no existe.", "datos": None}
    # Mi postulación sigue igual.
    assert yo.get("/api/postulaciones").json()["datos"][0]["Estado"] == "Postulado"


def test_el_correo_sale_del_token_no_del_cuerpo():
    c, correo = nuevo_usuario()
    otro, otro_correo = nuevo_usuario()
    # Aunque el cuerpo traiga otro correo, se guarda en la cuenta de la sesión.
    r = c.post("/api/perfil/datos", json={
        "nombre": "Mía", "correo_contacto": correo, "ubicacion": "Medellín", "ocupacion": "Analista",
        "correo": otro_correo,
    }).json()
    assert r["ok"], r
    assert otro.get("/api/perfil").json()["datos"]["datos"] is None
    assert c.get("/api/perfil").json()["datos"]["datos"]["Nombre"] == "Mía"


# ---------------------------------------------------------------- perfil manual
def test_perfil_manual_y_obligatorios():
    c, correo = nuevo_usuario()
    r = c.post("/api/perfil/datos", json={"nombre": "", "correo_contacto": correo, "ubicacion": "", "ocupacion": "x"}).json()
    assert r["mensaje"] == "Completa los campos obligatorios: Nombre completo, Ubicación."
    r = c.post("/api/perfil/experiencia", json={
        "empresa": "Andes", "cargo": "Dev", "fecha_inicio": "2022-01-01", "fecha_fin": "2021-01-01",
        "funciones": "APIs", "habilidades": "Python"}).json()
    assert r["ok"] is False and "anterior" in r["mensaje"]
    r = c.post("/api/perfil/experiencia", json={
        "empresa": "Andes", "cargo": "Dev", "fecha_inicio": "2022-01-01",
        "funciones": "APIs", "habilidades": "Python", "modalidad": "Sin especificar"}).json()
    assert r == {"ok": True, "mensaje": "Experiencia añadida correctamente al perfil", "datos": None}
    exp = c.get("/api/perfil").json()["datos"]["experiencia"]
    assert exp[0]["Titulo_puesto"] == "Dev" and exp[0]["Fecha_inicio"] == "2022-01-01"
    assert exp[0]["Modalidad_trabajo"] is None


# ---------------------------------------------------------------- archivos
def test_validacion_de_archivos():
    c, _ = nuevo_usuario()
    subir = lambda nombre, tipo: c.put(  # noqa: E731
        "/api/perfil/hoja-de-vida", files={"archivo": (nombre, archivo(nombre), tipo)}).json()
    assert subir("notas.txt", "text/plain")["mensaje"] == "Formato no válido: sube un archivo PDF o Word (.docx)."
    assert subir("falsa.pdf", "application/pdf")["ok"] is False
    assert subir("cv.pdf", "application/pdf")["ok"] is True
    assert c.get("/api/perfil/hoja-de-vida").json()["datos"]["nombre"] == "cv.pdf"


def test_descarga_con_tildes_rfc5987():
    c, _ = nuevo_usuario()
    c.put("/api/perfil/hoja-de-vida", files={"archivo": ("Hoja de vida Ángela.pdf", archivo("cv.pdf"), "application/pdf")})
    r = c.get("/api/perfil/hoja-de-vida/archivo")
    disp = r.headers["content-disposition"]
    assert "filename*=UTF-8''" in disp
    assert unquote(disp.split("filename*=UTF-8''")[1]) == "Hoja de vida Ángela.pdf"
    assert 'filename="Hoja de vida Angela.pdf"' in disp
    assert r.content == archivo("cv.pdf")


def test_carta_reemplaza_la_anterior():
    c, correo = nuevo_usuario()
    perfil_completo(correo)
    cv_guardado(correo)
    c.post(f"/api/vacantes/{id_vacante_abierta()}/postular")
    idp = c.get("/api/postulaciones").json()["datos"][0]["Id_postulacion"]
    assert c.put(f"/api/postulaciones/{idp}/carta",
                 files={"archivo": ("carta.pdf", archivo("carta.pdf"), "application/pdf")}).json()["ok"]
    r = c.put(f"/api/postulaciones/{idp}/carta",
              files={"archivo": ("carta_nueva.docx", archivo("carta_nueva.docx"), "application/octet-stream")}).json()
    assert r["ok"], r
    assert c.get(f"/api/postulaciones/{idp}/carta").json()["datos"]["Nombre_archivo"] == "carta_nueva.docx"
    # La carta es de 2 MB como máximo.
    r = c.put(f"/api/postulaciones/{idp}/carta",
              files={"archivo": ("pesada.pdf", archivo("pesada.pdf"), "application/pdf")}).json()
    assert r["ok"] is False and "el máximo es 2 MB" in r["mensaje"]


# ---------------------------------------------------------------- decisión 7
def test_extraer_no_guarda_y_confirmar_pide_revision():
    c, correo = nuevo_usuario()
    r = c.post("/api/importacion/extraer", data={"origen": "cv"},
               files={"archivo": ("cv_texto.pdf", archivo("cv_texto.pdf"), "application/pdf")}).json()
    assert r["ok"], r
    borrador = r["datos"]["borrador"]
    assert borrador["dudosos"]
    # Extraer no guardó nada.
    assert c.get("/api/perfil").json()["datos"]["datos"] is None
    # Con datos dudosos, confirmar sin «Revisé…» no guarda.
    r = c.post("/api/importacion/confirmar", json={"borrador": borrador}).json()
    assert r["mensaje"] == "Confirma que revisaste los datos que el agente marcó como dudosos."
    assert c.get("/api/perfil").json()["datos"]["datos"] is None
    r = c.post("/api/importacion/confirmar", json={"borrador": borrador, "revise": True}).json()
    assert r["ok"], r
    assert c.get("/api/perfil").json()["datos"]["datos"]["Nombre"] == borrador["nombre"]


def test_pdf_escaneado_avisa_sin_texto():
    c, _ = nuevo_usuario()
    r = c.post("/api/importacion/extraer", data={"origen": "cv"},
               files={"archivo": ("cv_escaneado.pdf", archivo("cv_escaneado.pdf"), "application/pdf")}).json()
    assert r == {"ok": True, "mensaje": None, "datos": {"sin_texto": True, "borrador": None}}


def test_linkedin_y_agente_caido():
    c, _ = nuevo_usuario()
    modo("error")
    r = c.post("/api/importacion/extraer", data={"origen": "linkedin"},
               files={"archivo": ("linkedin_perfil.pdf", archivo("linkedin_perfil.pdf"), "application/pdf")}).json()
    assert r["ok"] is False and r["mensaje"]
    modo("normal")
    r = c.post("/api/importacion/extraer", data={"origen": "linkedin"},
               files={"archivo": ("linkedin_perfil.pdf", archivo("linkedin_perfil.pdf"), "application/pdf")}).json()
    assert r["ok"], r
    assert r["datos"]["borrador"]["titular"] == "Backend Developer"


def test_recomendaciones_no_guardan_decisiones():
    c, correo = nuevo_usuario()
    perfil_completo(correo)
    estado = c.get("/api/recomendaciones/estado").json()["datos"]
    assert len(estado["base"]) == 64 and estado["candidatas"]
    r = c.post("/api/recomendaciones/generar").json()
    assert r["ok"], r
    assert r["datos"]["recomendaciones"]
    assert r["datos"]["base"] == estado["base"]
    assert sql("SELECT COUNT(*) FROM Recomendaciones WHERE Correos_recomendacion=%s", (correo,))[0][0] == 0
    id_v = r["datos"]["recomendaciones"][0]["vacante"]["Id_vacante"]
    assert c.post(f"/api/recomendaciones/{id_v}/decision", json={"decision": "Interesa", "motivo": "x"}).json()["ok"]
    assert [v["Id_vacante"] for v in c.get("/api/recomendaciones/interes").json()["datos"]] == [id_v]


def test_cv_generado_solo_se_guarda_al_confirmar():
    c, correo = nuevo_usuario()
    perfil_completo(correo)
    sql("INSERT INTO Experiencia(Correos_experiencia,Nombre_empresa,Titulo_puesto,Fecha_inicio,Descripcion_funciones,Habilidades)"
        " VALUES (%s,'Andes','Dev','2022-01-01','APIs','Python, SQL')", (correo,))
    r = c.post("/api/cv/borrador").json()
    assert r["ok"], r
    cv = r["datos"]["cv"]
    assert cv and c.get("/api/perfil/hoja-de-vida").json()["datos"] is None
    doc = c.post("/api/cv/documento", json={"cv": cv})
    assert doc.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert c.get("/api/perfil/hoja-de-vida").json()["datos"] is None
    assert c.post("/api/cv/confirmar", json={"cv": cv}).json()["ok"]
    assert c.get("/api/perfil/hoja-de-vida").json()["datos"]["nombre"].startswith("CV ")


def test_cv_con_perfil_incompleto_lista_faltantes():
    c, _ = nuevo_usuario()
    r = c.post("/api/cv/borrador").json()
    assert r["ok"] and r["datos"]["cv"] is None and r["datos"]["faltantes"]


# ---------------------------------------------------------------- postulaciones
def test_postular_sin_perfil_explica_que_falta():
    c, _ = nuevo_usuario()
    r = c.post(f"/api/vacantes/{id_vacante_abierta()}/postular").json()
    assert r["ok"] is False and r["mensaje"].startswith("Para postularte necesitas completar tu perfil")


def test_estado_deshacer_entrevista_y_prioridades():
    c, correo = nuevo_usuario()
    perfil_completo(correo)
    cv_guardado(correo)
    c.post(f"/api/vacantes/{id_vacante_abierta()}/postular")
    idp = c.get("/api/postulaciones").json()["datos"][0]["Id_postulacion"]
    assert c.put(f"/api/postulaciones/{idp}/estado", json={"estado": "Entrevista"}).json()["ok"]
    assert c.post(f"/api/postulaciones/{idp}/deshacer").json()["mensaje"] == "Deshiciste el último cambio."
    r = c.put(f"/api/postulaciones/{idp}/entrevista", json={"fecha": "2020-01-01T10:00"}).json()
    assert r["mensaje"] == "Esa fecha ya pasó: informa la fecha de tu próxima entrevista."
    # Un solo proceso activo: no se llama al agente.
    r = c.post("/api/prioridades").json()
    assert r["ok"] and r["datos"]["orden"] == [] and len(r["datos"]["procesos"]) == 1


def test_resumen_y_alerta():
    c, _ = nuevo_usuario()
    assert c.put("/api/alerta", json={}).json()["ok"] is False
    assert c.put("/api/alerta", json={"modalidad": "Virtual"}).json()["ok"]
    r = c.get("/api/resumen").json()
    assert r["ok"] and set(r["datos"]) == {"sin_leer", "recordatorios"}
    assert c.delete("/api/alerta").json()["mensaje"] == "Desactivaste tu alerta."


def test_guardar_y_quitar_vacante():
    c, _ = nuevo_usuario()
    idv = id_vacante_abierta()
    assert c.put(f"/api/vacantes/{idv}/guardada").json()["ok"]
    assert c.get(f"/api/vacantes/{idv}").json()["datos"]["guardada"] is True
    assert [g["Id_vacante"] for g in c.get("/api/guardadas").json()["datos"]] == [idv]
    assert c.delete(f"/api/vacantes/{idv}/guardada").json()["mensaje"] == "Quitaste la vacante de tus guardadas."
