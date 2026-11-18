"""Modelo de lenguaje SIMULADO, solo para pruebas (PROGENT_MODELO_SIMULADO=1).

Es el mismo del kit de pruebas (pruebas/app_simulada.py): responde según el prompt.
El modo se elige en /tmp/modo_modelo.txt: normal | vacio | basura | error | dudoso.
Cada llamada queda en /tmp/prompts_enviados.jsonl para revisar qué llegó al modelo.
"""
import json, pathlib, re  # noqa: E401

import anthropic
import httpx




class Bloque:
    type = "text"
    def __init__(self, texto): self.text = texto


class Respuesta:
    def __init__(self, texto): self.content = [Bloque(texto)]


def crear_falso(**kwargs):
    contenido = kwargs["messages"][0]["content"]
    with open("/tmp/prompts_enviados.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"system": kwargs.get("system"), "user": contenido}, ensure_ascii=False) + "\n")
    modo_archivo = pathlib.Path("/tmp/modo_modelo.txt")
    modo = modo_archivo.read_text().strip() if modo_archivo.exists() else "normal"
    if modo == "error":
        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com"))
    if modo == "basura":
        return Respuesta("Lo siento, no puedo ayudar con eso.")
    sistema = kwargs.get("system") or ""
    if "extractor de datos de hojas de vida" in sistema or "extractor de datos de perfiles de LinkedIn" in sistema:
        if modo == "vacio":
            return Respuesta("{}")
        if "LinkedIn" in sistema:
            perfil = {"nombre_completo": "Laura Gómez Prueba", "titular": "Backend Developer",
                      "contacto": {"correo": None, "telefono": None, "ciudad": "Medellín, Antioquia, Colombia", "enlaces": []},
                      "experiencia": [{"cargo": "Desarrolladora Python", "empresa": "Andes Digital", "fecha_inicio": "2022-01-01",
                                       "fecha_fin": None, "actual": True, "descripcion": None}],
                      "educacion": [{"titulo": "Ingeniería de Sistemas", "institucion": "Universidad EAFIT",
                                     "fecha_inicio": "2017", "fecha_fin": "2021-01-01", "en_curso": False}],
                      "habilidades": ["Python", "Docker"], "idiomas": [], "campos_dudosos": ["educacion[0].fecha_inicio"]}
        else:
            perfil = {"nombre_completo": "Laura Gómez Prueba", "titular": "Desarrolladora de software",
                      "contacto": {"correo": "laura.gomez@ejemplo.com", "telefono": "3015550000", "ciudad": "Medellín", "enlaces": []},
                      "experiencia": [{"cargo": "Desarrolladora Python", "empresa": "Andes Digital", "fecha_inicio": "2022-01-01",
                                       "fecha_fin": None, "actual": True, "descripcion": "APIs REST con FastAPI y MySQL."},
                                      {"cargo": "Practicante de sistemas", "empresa": "Nodo Ingeniería", "fecha_inicio": "2021-01-01",
                                       "fecha_fin": "2021-12-01", "actual": False, "descripcion": "Soporte y pruebas."}],
                      "educacion": [{"titulo": "Ingeniería de Sistemas", "institucion": "Universidad EAFIT",
                                     "fecha_inicio": "2017-01-01", "fecha_fin": "2021-01-01", "en_curso": False}],
                      "habilidades": ["Python", "SQL", "Git"], "idiomas": [{"idioma": "Inglés", "nivel": "B2"}],
                      "campos_dudosos": ["experiencia[0].fecha_inicio", "educacion[0].fecha_fin"]}
        return Respuesta(json.dumps(perfil, ensure_ascii=False))
    if "redactor de hojas de vida" in (kwargs.get("system") or ""):
        perfil = json.loads(re.search(r"<perfil>(.*)</perfil>", contenido, re.S).group(1))
        if modo == "vacio":
            return Respuesta('{"resumen": "", "experiencias": [], "habilidades": [], "secciones_dudosas": []}')
        experiencias = [{"indice": 0, "logros": ["Desarrollé APIs REST con FastAPI.", "Automaticé pruebas con Pytest."]}]
        experiencias += [{"indice": e["indice"], "logros": []} for e in perfil["experiencia"][1:]]
        return Respuesta(json.dumps({
            "resumen": "Desarrolladora backend con experiencia en servicios web y bases de datos.",
            "experiencias": experiencias,
            "habilidades": ["Python", "SQL", "Git"],
            "secciones_dudosas": ["habilidades"],
        }, ensure_ascii=False))
    if "<vacantes_interes>" in contenido:
        if modo == "vacio":
            return Respuesta('{"sugerencias": []}')
        perfil = json.loads(re.search(r"<perfil>(.*)</perfil>", contenido, re.S).group(1))
        interes = json.loads(re.search(r"<vacantes_interes>(.*)</vacantes_interes>", contenido, re.S).group(1))
        exp = perfil["experiencia"][0]["id_experiencia"]
        v = interes[0]["id_vacante"]
        sugs = [
            {"campo": "ocupacion", "id_experiencia": None, "propuesta": "Desarrolladora backend con experiencia en Python y APIs REST",
             "motivo": f"«{interes[0]['cargo']}» busca un perfil backend y tu titular no lo dice.", "vacantes": [v, 999], "seguro": True},
            {"campo": "funciones", "id_experiencia": exp, "propuesta": "Diseñé y mantuve APIs REST con FastAPI y MySQL, con despliegues semanales.",
             "motivo": "Las vacantes piden MySQL y trabajo ágil; tus funciones no lo mencionan.", "vacantes": [v], "seguro": True},
            {"campo": "habilidades", "id_experiencia": exp, "propuesta": "python, Docker, CI/CD",
             "motivo": "Piden Docker y CI/CD, pero tu perfil no los muestra.", "vacantes": [v], "seguro": False},
            {"campo": "educacion", "id_experiencia": None, "propuesta": "Maestría inventada", "motivo": "campo no permitido", "seguro": True},
            {"campo": "funciones", "id_experiencia": 99999, "propuesta": "De otra persona", "motivo": "id ajeno", "seguro": True},
            {"campo": "habilidades", "id_experiencia": exp, "propuesta": "SQL, git", "motivo": "ya las tiene", "seguro": True},
            {"campo": "ocupacion", "propuesta": "Sin motivo", "motivo": "", "seguro": True},
        ]
        return Respuesta("```json\n" + json.dumps({"sugerencias": sugs}, ensure_ascii=False) + "\n```")
    if "<vacante_evaluar>" in contenido:
        perfil = json.loads(re.search(r"<perfil>(.*)</perfil>", contenido, re.S).group(1))
        if modo == "vacio":
            return Respuesta('{"criterios": [], "informacion_suficiente": true}')
        criterios = [
            {"requisito": "Experiencia con Python", "cumple": "si", "dato_perfil": "Experiencia como Desarrolladora Python", "seguro": True},
            {"requisito": "Django o FastAPI", "cumple": "parcial", "dato_perfil": "Funciones: APIs REST con FastAPI", "seguro": False},
            {"requisito": "MySQL", "cumple": "no", "dato_perfil": None, "seguro": True},
            {"requisito": "Git", "cumple": "sí", "dato_perfil": None, "seguro": True},
            {"requisito": "", "cumple": "si", "dato_perfil": "x", "seguro": True},
            {"requisito": "Inglés", "cumple": "tal vez", "dato_perfil": "x", "seguro": True},
        ]
        return Respuesta(json.dumps({"criterios": criterios, "informacion_suficiente": bool(perfil["experiencia"])}, ensure_ascii=False))
    if "<procesos>" in contenido:
        if modo == "vacio":
            return Respuesta('{"orden": [], "resumen": ""}')
        procesos = json.loads(re.search(r"<procesos>(.*)</procesos>", contenido, re.S).group(1))
        peso = {"Oferta": 0, "Entrevista": 1, "En revision": 2, "Postulado": 3}
        procesos.sort(key=lambda x: peso[x["etapa"]])
        orden = [{"id_proceso": x["id_proceso"], "motivo": f"«{x['cargo']}» está en {x['etapa']}.", "seguro": i == 0}
                 for i, x in enumerate(procesos[:-1])]
        orden += [{"id_proceso": 999, "motivo": "inventado", "seguro": True},
                  {"id_proceso": procesos[0]["id_proceso"], "motivo": "repetido", "seguro": True}]
        return Respuesta(json.dumps({"orden": orden, "resumen": "Primero lo que espera tu respuesta, luego lo que necesita preparación."}, ensure_ascii=False))
    if "<formulario>" in contenido:
        campos = [
            {"pregunta": "Nombre completo", "tipo": "dato_personal", "dato_personal": "nombre", "respuesta": "Inventado"},
            {"pregunta": "Correo electrónico", "tipo": "dato_personal", "dato_personal": "correo"},
            {"pregunta": "¿Qué experiencia tienes con Python?", "tipo": "respuesta",
             "respuesta": "He desarrollado APIs REST con Python y FastAPI.", "seguro": True},
            {"pregunta": "¿Por qué quieres trabajar con nosotros?", "tipo": "respuesta",
             "respuesta": "Me interesa el sector de pagos.", "seguro": False,
             "nota": "tu perfil no dice nada sobre esta empresa"},
            {"pregunta": "Número de tarjeta profesional", "tipo": "no_sabe", "nota": "Tu perfil no tiene ese dato."},
            {"pregunta": "Fecha de nacimiento", "tipo": "dato_personal", "dato_personal": "fecha_nacimiento"},
            {"pregunta": "", "tipo": "respuesta", "respuesta": "sin pregunta"},
        ]
        if modo == "vacio":
            campos = []
        return Respuesta(json.dumps({"campos": campos}, ensure_ascii=False))
    if modo == "vacio":
        return Respuesta('```json\n{"recomendaciones": []}\n```')
    vacantes = json.loads(re.search(r"<vacantes>(.*)</vacantes>", contenido, re.S).group(1))
    ids = [v["id_vacante"] for v in vacantes]
    recs = [
        {"id_vacante": ids[0], "motivo": f"Tu experiencia en Python encaja con «{vacantes[0]['cargo']}».", "seguro": True},
        {"id_vacante": 999, "motivo": "Vacante inventada", "seguro": True},
        {"id_vacante": ids[0], "motivo": "Repetida", "seguro": True},
    ]
    if len(ids) > 1:
        recs.append({"id_vacante": ids[1], "motivo": f"Solo coincide en parte con «{vacantes[1]['cargo']}»: tienes SQL pero no el resto.", "seguro": False})
    if len(ids) > 2:
        recs.append({"id_vacante": ids[2], "motivo": "", "seguro": True})
    if modo == "dudoso":
        for r in recs:
            r["seguro"] = False
    return Respuesta("```json\n" + json.dumps({"recomendaciones": recs}, ensure_ascii=False) + "\n```")




def activar():
    """Reemplaza el cliente de Anthropic de graph por el simulado."""
    import graph

    graph.cliente.messages.create = crear_falso
