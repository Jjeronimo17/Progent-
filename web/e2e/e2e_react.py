"""Prueba de punta a punta de la app en React (Playwright + API con el modelo SIMULADO).

Requisitos: la API en :8000 con PROGENT_MODELO_SIMULADO=1, el frontend en :4173 (vite preview)
o :5173 (vite dev) y la base de prueba cargada con db/schema.sql.
Uso:  PROGENT_URL=http://localhost:4173 python3 web/e2e/e2e_react.py
Cada bloque imprime "OK ..." cuando pasa; cualquier fallo corta la prueba con el detalle.
"""
import os, re, subprocess, uuid  # noqa: E401
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

URL = os.getenv("PROGENT_URL", "http://localhost:4173")
ARCHIVOS = Path(__file__).resolve().parents[2] / "api" / "tests" / "archivos"
CAPTURAS = Path(os.getenv("PROGENT_CAPTURAS", "/tmp/capturas"))
CAPTURAS.mkdir(parents=True, exist_ok=True)
MYSQL = os.getenv("PROGENT_MYSQL", "sudo mysql").split()


def sql(q):
    return subprocess.run(MYSQL + ["-N", "--default-character-set=utf8mb4", "Progent_Usuarios", "-e", q],
                          check=True, capture_output=True, text=True).stdout.strip()


def modo(m): Path("/tmp/modo_modelo.txt").write_text(m)


def entrar(page, preparar=None):
    correo = f"e2e_{uuid.uuid4().hex[:8]}@ejemplo.com"
    page.goto(URL + "/login")
    page.get_by_label("Correo electrónico").fill(correo)
    page.get_by_label("Contraseña").fill("ClaveSegura123")
    page.get_by_role("button", name="Crear cuenta").click()
    expect(page.get_by_text("Registro exitoso")).to_be_visible()
    if preparar:
        preparar(correo)
    page.get_by_role("tab", name="Iniciar sesión").click()
    page.get_by_label("Correo electrónico").fill(correo)
    page.get_by_label("Contraseña").fill("ClaveSegura123")
    page.get_by_role("button", name="Iniciar sesión").click()
    page.wait_for_url("**/perfil")
    return correo


def menu(page, texto):
    page.get_by_role("link", name=re.compile(rf"^{texto}( \(\d+\))?$")).filter(visible=True).first.click()


def perfil_completo(correo):
    sql(f"INSERT INTO informacion_usuarios VALUES ('{correo}','Persona Prueba',30,'3000000000','{correo}','Medellín','Desarrolladora Python')")
    sql(f"INSERT INTO Experiencia(Correos_experiencia,Nombre_empresa,Titulo_puesto,Fecha_inicio,Descripcion_funciones,Habilidades) "
        f"VALUES ('{correo}','Andes','Desarrolladora Python','2022-01-01','APIs REST con FastAPI','Python, SQL')")
    sql(f"INSERT INTO Educacion(Correos_educacion,Institucion_educativa,Titulo_Carrera_Grado,Fecha_inicio,Estado_estudio) "
        f"VALUES ('{correo}','Universidad Inventada','Ingeniería','2020-01-01','Graduado')")


def cv_guardado(correo):
    sql(f"INSERT INTO archivos_usuarios VALUES ('{correo}','cv.pdf','application/pdf',x'255044462D312E340A')")


def postular_sql(correo, id_vacante, estado="Postulado"):
    sql(f"INSERT INTO Postulaciones(Correos_postulacion,Id_vacante_postulacion,Fecha_postulacion,Estado) "
        f"VALUES ('{correo}',{id_vacante},NOW(),'{estado}')")
    return int(sql(f"SELECT Id_postulacion FROM Postulaciones WHERE Correos_postulacion='{correo}' AND Id_vacante_postulacion={id_vacante}"))


modo("normal")
with sync_playwright() as p:
    navegador = p.chromium.launch(args=["--no-sandbox"])
    page = navegador.new_page(viewport={"width": 1280, "height": 1000})
    errores_js = []
    page.on("pageerror", lambda e: errores_js.append(str(e)))

    # ------------------------------------------------------------ Vacantes y detalle
    correo = entrar(page)
    menu(page, "Vacantes")
    expect(page.get_by_role("heading", name="Vacantes disponibles")).to_be_visible()
    expect(page.get_by_text(re.compile(r"^\d+ vacantes disponibles$"))).to_be_visible()
    page.get_by_label("Buscar por palabra clave").fill("Python")
    expect(page.get_by_text(re.compile(r"coinciden? con «Python»$"))).to_be_visible()
    page.get_by_label("Modalidad").select_option("Hibrido")
    expect(page.get_by_text(re.compile(r"los filtros y coinciden? con «Python»|Sin resultados"))).to_be_visible()
    page.get_by_role("button", name="Crear alerta con estos filtros").click()
    expect(page.get_by_text(re.compile(r"Alerta guardada.*Criterios: «Python» · Híbrido\."))).to_be_visible()
    page.get_by_label("Buscar por palabra clave").fill("zzzz-no-existe")
    expect(page.get_by_text(re.compile("Sin resultados: ninguna vacante con «zzzz-no-existe» cumple los filtros"))).to_be_visible()
    print("OK vacantes: listado, búsqueda, filtros, alerta y estado vacío")

    page.goto(URL + "/vacantes/1")
    expect(page.get_by_role("heading", name="Desarrollador Backend Python")).to_be_visible()
    page.get_by_role("button", name="Guardar vacante").click()
    expect(page.get_by_text("Guardaste esta vacante. La encuentras en Guardadas.")).to_be_visible()
    expect(page.get_by_role("button", name="Quitar de guardadas")).to_be_visible()
    page.get_by_role("button", name="Postularme").click()
    expect(page.get_by_text(re.compile("^Para postularte necesitas completar tu perfil"))).to_be_visible()
    page.get_by_role("button", name="Mi compatibilidad con esta vacante").click()
    page.get_by_role("button", name="Calcular mi compatibilidad").click()
    expect(page.get_by_text(re.compile("Tu perfil no tiene información para compararlo"))).to_be_visible()
    print("OK detalle: guardar, postular sin perfil explica qué falta, compatibilidad con perfil vacío")

    # ------------------------------------------------------------ Guardadas
    menu(page, "Guardadas")
    expect(page.get_by_role("heading", name="Desarrollador Backend Python")).to_be_visible()
    page.get_by_role("button", name="Quitar").click()
    expect(page.get_by_text("Quitaste la vacante de tus guardadas.")).to_be_visible()
    expect(page.get_by_text("Todavía no has guardado vacantes.")).to_be_visible()
    print("OK guardadas: lista, quitar y estado vacío")

    # ------------------------------------------------------------ Postular con perfil + compatibilidad
    page.get_by_role("button", name="Cerrar sesión").first.click(); page.wait_for_url("**/login")
    correo = entrar(page, lambda c: (perfil_completo(c), cv_guardado(c)))
    page.goto(URL + "/vacantes/1")
    page.get_by_role("button", name="Mi compatibilidad con esta vacante").click()
    page.get_by_role("button", name="Calcular mi compatibilidad").click()
    expect(page.get_by_text(re.compile(r"^Compatibilidad: (Alta|Media|Baja) \(\d+ %\)"))).to_be_visible()
    expect(page.get_by_role("progressbar")).to_be_visible()
    expect(page.get_by_text(re.compile("^Me basé en:|Tu perfil no lo menciona.")).first).to_be_visible()
    page.screenshot(path=str(CAPTURAS / "20_compatibilidad.png"), full_page=True)
    expect(page.get_by_text("cv.pdf (guardada en tu perfil)")).to_be_visible()
    page.get_by_role("button", name="Postularme").click()
    expect(page.get_by_text(re.compile("Ya te postulaste a esta vacante el"))).to_be_visible()
    expect(page.get_by_text("Hoja de vida asociada a esta postulación:")).to_be_visible()
    print("OK postularse: compatibilidad con nivel, % y base de cada requisito; postulación con su hoja de vida")

    # ------------------------------------------------------------ Recomendaciones
    menu(page, "Recomendaciones")
    expect(page.get_by_role("button", name="Me interesa").first).to_be_visible(timeout=15000)
    page.screenshot(path=str(CAPTURAS / "21_recomendaciones.png"), full_page=True)
    n_antes = page.get_by_role("button", name="Me interesa").count()
    page.get_by_role("button", name="Me interesa").first.click()
    expect(page.get_by_text("La marcaste como de interés.")).to_be_visible()
    expect(page.get_by_role("heading", name="Vacantes que marcaste de interés")).to_be_visible()
    expect(page.get_by_role("button", name="Me interesa")).to_have_count(n_antes - 1)
    page.get_by_role("button", name="Postularme").first.click()
    expect(page.get_by_text(re.compile("¿Confirmas que quieres postularte a"))).to_be_visible()
    page.get_by_role("button", name="Cancelar").click()
    expect(page.get_by_text(re.compile("¿Confirmas que quieres postularte a"))).to_have_count(0)
    page.get_by_role("button", name="Postularme").first.click()
    page.get_by_role("button", name="Confirmar postulación").click()
    expect(page.get_by_text(re.compile(r"^Te postulaste a «.+»\. La encuentras en Mis postulaciones\.$"))).to_be_visible()
    # Volver a la sección no vuelve a llamar al agente si nada cambió (#25).
    enviados = Path("/tmp/prompts_enviados.jsonl")
    llamadas = len(enviados.read_text(encoding="utf-8").splitlines()) if enviados.exists() else 0
    menu(page, "Vacantes"); menu(page, "Recomendaciones")
    expect(page.get_by_role("heading", name="Vacantes recomendadas")).to_be_visible()
    page.wait_for_timeout(1500)
    assert len(enviados.read_text(encoding="utf-8").splitlines()) == llamadas, "volvió a llamar al agente sin cambios"
    print("OK recomendaciones: solas al entrar, me interesa, confirmar/cancelar postulación (#27)")

    # ------------------------------------------------------------ Mis postulaciones
    postular_sql(correo, 4, "Entrevista")
    menu(page, "Mis postulaciones")
    expect(page.get_by_role("heading", name=re.compile(r"Postulado \(\d\)"))).to_be_visible()
    expect(page.get_by_text("Sin postulaciones en esta etapa.").first).to_be_visible()
    tarjeta = page.get_by_role("article").filter(has_text="Desarrollador Backend Python")
    tarjeta.get_by_role("button", name="Actualizar estado").click()
    tarjeta.get_by_label("Nueva etapa").select_option("En revision")
    tarjeta.get_by_role("button", name="Guardar estado").click()
    expect(page.get_by_text("Estado actualizado a «En revisión». «Desarrollador Backend Python» ahora aparece en esa etapa.")).to_be_visible()
    expect(page.get_by_role("heading", name="En revisión (1)")).to_be_visible()
    tarjeta = page.get_by_role("article").filter(has_text="Desarrollador Backend Python")
    tarjeta.get_by_role("button", name="Actualizar estado").click()
    tarjeta.get_by_role("button", name="Deshacer último cambio (volver a «Postulado»)").click()
    expect(page.get_by_text("Deshiciste el último cambio. «Desarrollador Backend Python» volvió a «Postulado».")).to_be_visible()
    print("OK estado: cambiar, aviso arriba del panel, se mueve de etapa y deshacer (#21, #22, #23)")

    tarjeta = page.get_by_role("article").filter(has_text="Desarrollador Backend Python")
    tarjeta.get_by_role("button", name="Informar entrevista").click()
    tarjeta.get_by_label("Fecha de la entrevista").fill("2099-01-15")
    tarjeta.get_by_label("Hora").fill("10:30")
    tarjeta.get_by_role("button", name="Guardar entrevista").click()
    expect(tarjeta.get_by_text(re.compile("Guardaste tu entrevista del 15/01/2099 a las 10:30"))).to_be_visible()
    tarjeta.get_by_role("button", name="Carta de presentación").click()
    tarjeta.get_by_label(re.compile("Adjuntar carta de presentación")).set_input_files(str(ARCHIVOS / "carta.pdf"))
    tarjeta.get_by_role("button", name="Guardar carta").click()
    expect(tarjeta.get_by_text("Carta «carta.pdf» adjunta a tu postulación.")).to_be_visible()
    tarjeta.get_by_label(re.compile("Reemplazar la carta")).set_input_files(str(ARCHIVOS / "pesada.pdf"))
    tarjeta.get_by_role("button", name="Guardar carta").click()
    expect(tarjeta.get_by_text(re.compile("el máximo es 2 MB"))).to_be_visible()
    print("OK entrevista y carta (#18, #28)")

    tarjeta.get_by_role("button", name="Formulario de la vacante").click()
    tarjeta.get_by_label("Pega aquí el formulario de la vacante").fill(
        "Nombre completo\nCorreo electrónico\n¿Qué experiencia tienes con Python?\n¿Por qué quieres trabajar con nosotros?\nNúmero de tarjeta profesional")
    tarjeta.get_by_role("button", name="Llenar con el agente").click()
    expect(tarjeta.get_by_text("Respuestas propuestas por el agente. Edítalas, rechaza las que no sirvan y confirma.")).to_be_visible()
    expect(tarjeta.get_by_text("Dato tomado de tu perfil. No se envió al agente.").first).to_be_visible()
    expect(tarjeta.get_by_text(re.compile("^No estoy seguro de esta respuesta"))).to_be_visible()
    page.screenshot(path=str(CAPTURAS / "22_formulario.png"), full_page=True)
    tarjeta.get_by_role("button", name="Confirmar respuestas").click()
    expect(tarjeta.get_by_text(re.compile("^Completa o rechaza estas preguntas antes de confirmar"))).to_be_visible()
    vacias = tarjeta.get_by_role("textbox", name=re.compile(r"^Respuesta \d+$"))
    for i in range(vacias.count()):
        if not vacias.nth(i).input_value().strip():
            vacias.nth(i).fill("Dato escrito a mano")
    tarjeta.get_by_role("button", name="Confirmar respuestas").click()
    expect(tarjeta.get_by_text(re.compile(r"^Guardaste \d+ respuestas"))).to_be_visible()
    expect(tarjeta.get_by_text("Respuestas confirmadas")).to_be_visible()
    print("OK formulario (#19): propuesta, datos personales locales, dudosos, obligatorios y confirmar")

    page.get_by_role("button", name="¿Qué proceso atiendo primero?").click()
    page.get_by_role("button", name="Sugerir prioridades").click()
    expect(page.get_by_text(re.compile("^Por qué este orden:"))).to_be_visible()
    expect(page.get_by_text("Es solo una sugerencia del agente: no cambia nada en tus postulaciones.")).to_be_visible()
    page.screenshot(path=str(CAPTURAS / "23_postulaciones.png"), full_page=True)
    print("OK prioridades (#29)")

    # ------------------------------------------------------------ Notificaciones (#17)
    sql(f"UPDATE Alertas SET Fecha_creacion = NOW() - INTERVAL 1 DAY WHERE Correos_alerta='{correo}'") if sql(
        f"SELECT COUNT(*) FROM Alertas WHERE Correos_alerta='{correo}'") != "0" else None
    page.goto(URL + "/vacantes")
    page.get_by_label("Buscar por palabra clave").fill("Kotlin")
    page.get_by_role("button", name="Crear alerta con estos filtros").click()
    expect(page.get_by_text(re.compile("Alerta guardada"))).to_be_visible()
    nuevo_id = int(sql("SELECT COALESCE(MAX(Id_vacante),0)+1 FROM Vacantes"))
    sql("INSERT INTO Vacantes(Id_vacante,Cargo,Empresa,Ubicacion,Descripcion,Requisitos,Estado,Fecha_publicacion,Salario,Modalidad) "
        f"VALUES ({nuevo_id},'Desarrollador Kotlin','Empresa Nueva','Medellín','Apps con Kotlin','Kotlin','Abierta',CURDATE(),5000000,'Virtual')")
    menu(page, "Guardadas"); menu(page, "Notificaciones")
    expect(page.get_by_role("link", name="Notificaciones (1)").first).to_be_visible()
    expect(page.get_by_role("heading", name="Desarrollador Kotlin")).to_be_visible()
    expect(page.get_by_text("«Kotlin»")).to_be_visible()
    page.get_by_role("button", name="Marcar todas como leídas").click()
    expect(page.get_by_text("Notificaciones marcadas como leídas.")).to_be_visible()
    page.get_by_role("button", name="Desactivar alerta").click()
    expect(page.get_by_text("Desactivaste tu alerta.")).to_be_visible()
    print("OK notificaciones: contador en el menú, lista, marcar leídas, alerta y desactivarla")

    # ------------------------------------------------------------ Mejorar y generar CV
    sql(f"INSERT INTO Vacantes_guardadas(Correos_guardada,Id_vacante_guardada,Fecha_guardada) VALUES ('{correo}',2,NOW())")
    page.goto(URL + "/perfil/mejorar")
    expect(page.get_by_text(re.compile("^Se comparará con:"))).to_be_visible()
    page.get_by_role("button", name="Pedir sugerencias").click()
    expect(page.get_by_role("button", name="Aplicar a mi perfil").first.or_(page.get_by_text(re.compile("ya encaja")))).to_be_visible(timeout=15000)
    if page.get_by_role("button", name="Descartar").count():
        page.get_by_role("button", name="Descartar").first.click()
        expect(page.get_by_text("Descartaste la sugerencia; tu perfil no cambió.")).to_be_visible()
    print("OK mejorar (#24)")

    page.goto(URL + "/perfil/generar-cv")
    page.get_by_role("button", name="Generar mi CV").click()
    expect(page.get_by_label("Perfil profesional")).to_be_visible(timeout=15000)
    page.get_by_role("button", name="Rechazar").click()
    expect(page.get_by_text("Rechazaste el CV generado: no se guardó nada.")).to_be_visible()
    page.get_by_role("button", name="Generar mi CV").click()
    expect(page.get_by_label("Titular")).to_be_visible(timeout=15000)
    with page.expect_download() as descarga:
        page.get_by_role("button", name="Descargar CV (.docx)").click()
    assert descarga.value.suggested_filename.endswith(".docx"), descarga.value.suggested_filename
    page.get_by_role("button", name="Confirmar CV").click()
    expect(page.get_by_text(re.compile(r"^Guardaste «CV .+\.docx»"))).to_be_visible()
    print("OK generar CV (#7): rechazar no guarda, descargar .docx y confirmar")

    # ------------------------------------------------------------ Móvil
    movil = navegador.new_page(viewport={"width": 390, "height": 844}, storage_state=page.context.storage_state())
    movil.goto(URL + "/postulaciones")
    expect(movil.get_by_role("heading", name="Mis postulaciones")).to_be_visible()
    movil.screenshot(path=str(CAPTURAS / "24_movil_postulaciones.png"))
    print("OK móvil")

    assert not errores_js, errores_js
    navegador.close()
print("TODO OK")
