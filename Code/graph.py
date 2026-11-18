"""Grafo del agente de extraccion de perfil (Progent - prueba de concepto).

Flujo:  leer_pdf  ->  extraer  ->  validar  ->  END

El grafo es intencionalmente pequeño: la prueba de concepto busca demostrar que el
ambiente funciona de punta a punta, no cubrir todos los casos.
"""

import io
import json
import os
from typing import Any, TypedDict
from docx import Document
import anthropic
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from pypdf import PdfReader
from typing import Literal
from prompts import SYSTEM_EXTRACCION, USER_EXTRACCION, SYSTEM_EXTRACCION_LINKEDIN

load_dotenv()

MODELO = os.getenv("MODELO", "claude-haiku-4-5-20251001")
cliente = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno


class EstadoPerfil(TypedDict, total=False):
    """Estado que viaja por el grafo."""

    pdf_bytes: bytes
    docx_bytes: bytes
    texto: str
    perfil: dict[str, Any]
    errores: list[str]
    origen: str
    tipo: Literal["pdf", "docx"]


# --------------------------------------------------------------------------
# Nodo 1: sacar el texto del PDF
# --------------------------------------------------------------------------
def leer_pdf(estado: EstadoPerfil) -> EstadoPerfil:
    if estado["tipo"].lower() == "docx":
        lector = Document(io.BytesIO(estado["docx_bytes"]))
        parrafos = [p.text for p in lector.paragraphs]
        for p in lector.tables:
            for r in p.rows:
                for c in r.cells:
                    parrafos.append(c.text)
        texto = "\n".join(parrafos).strip()
    else:
        lector = PdfReader(io.BytesIO(estado["pdf_bytes"]))
        paginas = [(p.extract_text() or "") for p in lector.pages]
        texto = "\n".join(paginas).strip()

    errores = list(estado.get("errores", []))
    if len(texto) < 50:
        errores.append(
            "El PDF no tiene texto seleccionable (puede ser un escaneo). "
            "Prueba con otro archivo."
        )
    return {"texto": texto, "errores": errores}


# --------------------------------------------------------------------------
# Nodo 2: pedirle al modelo que estructure el texto
# --------------------------------------------------------------------------
def extraer(estado: EstadoPerfil) -> EstadoPerfil:
    if estado.get("errores"):
        return {}

    respuesta = cliente.messages.create(
        model=MODELO,
        max_tokens=4000,
        system=SYSTEM_EXTRACCION,
        messages=[
            {"role": "user", "content": USER_EXTRACCION.format(texto=estado["texto"])},
        ],
    )

    bloques = [b.text for b in respuesta.content if b.type == "text"]
    errores = list(estado.get("errores", []))
    if not bloques:
        errores.append("El modelo no devolvio texto")
        return {"errores": errores}
    crudo = "\n".join(bloques).strip()

    if crudo.startswith("```"):
        crudo = crudo.split("```")[1]
        if crudo.startswith("json"):
            crudo = crudo[4:]
        crudo = crudo.strip()

    inicio, fin = crudo.find("{"), crudo.rfind("}")
    if inicio != -1 and fin != -1:
        crudo = crudo[inicio : fin + 1]

    try:
        perfil = json.loads(crudo)
    except json.JSONDecodeError as e:
        errores = list(estado.get("errores", []))
        errores.append(f"El modelo no devolvio JSON valido: {e}")
        return {"errores": errores}

    return {"perfil": perfil}


def extraerLinkedin(estado: EstadoPerfil) -> EstadoPerfil:
    if estado.get("errores"):
        return {}

    respuesta = cliente.messages.create(
        model=MODELO,
        max_tokens=4000,
        system=SYSTEM_EXTRACCION_LINKEDIN,
        messages=[
            {"role": "user", "content": USER_EXTRACCION.format(texto=estado["texto"])},
        ],
    )

    bloques = [b.text for b in respuesta.content if b.type == "text"]
    errores = list(estado.get("errores", []))
    if not bloques:
        errores.append("El modelo no devolvio texto")
        return {"errores": errores}
    crudo = "\n".join(bloques).strip()
    if crudo.startswith("```"):
        crudo.split("```")[1]
        if crudo.startswith("json"):
            crudo = crudo[4:]
        crudo = crudo.strip()

    inicio, fin = crudo.find("{"), crudo.rfind("}")
    if inicio != -1 and fin != -1:
        crudo = crudo[inicio : fin + 1]

    try:
        perfil = json.loads(crudo)
    except json.JSONDecodeError as e:
        errores = list(estado.get("errores", []))
        errores.append(f"El modelo no devolvio el JSON valido {e}")
        return {"errores": errores}

    return {"perfil": perfil}


def siguientePaso(estado: EstadoPerfil) -> Literal["cv", "linkedin"]:
    if "cv" in estado["origen"]:
        return "cv"
    return "linkedin"


# --------------------------------------------------------------------------
# Nodo 3: revisar que el JSON tenga la forma esperada
# --------------------------------------------------------------------------
CLAVES = ["nombre_completo", "contacto", "experiencia", "educacion", "habilidades"]


def validar(estado: EstadoPerfil) -> EstadoPerfil:
    if estado.get("errores"):
        return {}

    perfil = estado.get("perfil", {})
    faltantes = [c for c in CLAVES if c not in perfil]
    errores = list(estado.get("errores", []))
    if faltantes:
        errores.append("Faltan claves en la respuesta: " + ", ".join(faltantes))
    if not perfil.get("nombre_completo"):
        errores.append("No se pudo identificar el nombre en la hoja de vida.")

    return {"errores": errores}


# --------------------------------------------------------------------------
# Armado del grafo
# --------------------------------------------------------------------------
def construir_grafo():
    g = StateGraph(EstadoPerfil)
    g.add_node("leer_pdf", leer_pdf)
    g.add_node("extraer", extraer)
    g.add_node("validar", validar)
    g.add_node("extraerLinkedin", extraerLinkedin)

    g.set_entry_point("leer_pdf")
    g.add_conditional_edges(
        "leer_pdf", siguientePaso, {"cv": "extraer", "linkedin": "extraerLinkedin"}
    )
    g.add_edge("extraer", "validar")
    g.add_edge("validar", END)
    g.add_edge("extraerLinkedin", "validar")
    g.add_edge("validar", END)

    return g.compile()


grafo = construir_grafo()


def procesar_cv(pdf_bytes: bytes) -> EstadoPerfil:
    """Punto de entrada usado por la interfaz."""
    return grafo.invoke({"pdf_bytes": pdf_bytes, "errores": []})


# ==========================================================================
# Agente de recomendación de vacantes (historia #11)
#
# Flujo:  recomendar  ->  validar_recomendaciones  ->  END
#
# Recibe el perfil SIN datos personales (decisión 6): no llegan nombre,
# teléfono, correos, ubicación ni edad. Lo arma recomendaciones.py.
# ==========================================================================
from prompts import SYSTEM_RECOMENDACION, USER_RECOMENDACION


class EstadoRecomendacion(TypedDict, total=False):
    """Estado que viaja por el grafo de recomendación."""

    perfil: dict[str, Any]
    preferencias: dict[str, Any]
    vacantes: list[dict[str, Any]]
    recomendaciones: list[dict[str, Any]]
    errores: list[str]


def leer_json_modelo(crudo: str) -> dict:
    """Saca el objeto JSON de la respuesta del modelo (puede venir entre ```)."""
    crudo = crudo.strip()
    inicio, fin = crudo.find("{"), crudo.rfind("}")
    if inicio == -1 or fin == -1:
        raise json.JSONDecodeError("No hay un objeto JSON", crudo, 0)
    return json.loads(crudo[inicio : fin + 1])


def recomendar(estado: EstadoRecomendacion) -> EstadoRecomendacion:
    errores = list(estado.get("errores", []))
    vacantes = [
        {
            "id_vacante": v["Id_vacante"],
            "cargo": v["Cargo"],
            "empresa": v["Empresa"],
            "descripcion": v["Descripcion"],
            "requisitos": v["Requisitos"],
        }
        for v in estado["vacantes"]
    ]
    mensaje = USER_RECOMENDACION.format(
        perfil=json.dumps(estado["perfil"], ensure_ascii=False, indent=2),
        preferencias=json.dumps(estado.get("preferencias", {}), ensure_ascii=False),
        vacantes=json.dumps(vacantes, ensure_ascii=False, indent=2),
    )

    try:
        respuesta = cliente.messages.create(
            model=MODELO,
            max_tokens=2000,
            system=SYSTEM_RECOMENDACION,
            messages=[{"role": "user", "content": mensaje}],
        )
    except anthropic.APIError as e:
        print(f"Fallo en la llamada al modelo {e}")
        errores.append("El agente no respondió. Intenta de nuevo en unos minutos.")
        return {"errores": errores}

    texto = "\n".join(b.text for b in respuesta.content if b.type == "text")
    try:
        datos = leer_json_modelo(texto)
    except json.JSONDecodeError:
        errores.append("El agente devolvió una respuesta que no se pudo leer. Intenta de nuevo.")
        return {"errores": errores}

    recomendaciones = datos.get("recomendaciones")
    if not isinstance(recomendaciones, list):
        errores.append("El agente devolvió una respuesta incompleta. Intenta de nuevo.")
        return {"errores": errores}
    return {"recomendaciones": recomendaciones}


def validar_recomendaciones(estado: EstadoRecomendacion) -> EstadoRecomendacion:
    """Deja solo recomendaciones de vacantes enviadas, sin repetir y con motivo."""
    if estado.get("errores"):
        return {}

    vacantes = {v["Id_vacante"]: v for v in estado["vacantes"]}
    validas, vistas = [], set()
    for r in estado.get("recomendaciones", []):
        if not isinstance(r, dict):
            continue
        try:
            id_vacante = int(r.get("id_vacante"))
        except (TypeError, ValueError):
            continue
        motivo = str(r.get("motivo") or "").strip()
        if id_vacante not in vacantes or id_vacante in vistas or not motivo:
            continue
        vistas.add(id_vacante)
        validas.append(
            {
                "vacante": vacantes[id_vacante],
                "motivo": motivo,
                "seguro": r.get("seguro") is True,
            }
        )
    return {"recomendaciones": validas[:5]}


def construir_grafo_recomendacion():
    g = StateGraph(EstadoRecomendacion)
    g.add_node("recomendar", recomendar)
    g.add_node("validar_recomendaciones", validar_recomendaciones)
    g.set_entry_point("recomendar")
    g.add_edge("recomendar", "validar_recomendaciones")
    g.add_edge("validar_recomendaciones", END)
    return g.compile()


grafo_recomendacion = construir_grafo_recomendacion()


def recomendar_vacantes(perfil, preferencias, vacantes) -> EstadoRecomendacion:
    """Punto de entrada usado por la interfaz de recomendaciones."""
    return grafo_recomendacion.invoke(
        {"perfil": perfil, "preferencias": preferencias, "vacantes": vacantes, "errores": []}
    )


# ==========================================================================
# Agente que completa formularios de postulación (historia #19)
#
# Flujo:  interpretar_formulario  ->  validar_formulario  ->  END
#
# Recibe el perfil SIN datos personales (decisión 6). Los campos personales
# solo se marcan; formularios.py los llena localmente con el perfil.
# ==========================================================================
from prompts import DATOS_PERSONALES, SYSTEM_FORMULARIO, USER_FORMULARIO


class EstadoFormulario(TypedDict, total=False):
    """Estado que viaja por el grafo del formulario."""

    formulario: str
    perfil: dict[str, Any]
    campos: list[dict[str, Any]]
    errores: list[str]


def interpretar_formulario(estado: EstadoFormulario) -> EstadoFormulario:
    errores = list(estado.get("errores", []))
    mensaje = USER_FORMULARIO.format(
        perfil=json.dumps(estado["perfil"], ensure_ascii=False, indent=2),
        formulario=estado["formulario"],
    )
    try:
        respuesta = cliente.messages.create(
            model=MODELO,
            max_tokens=4000,
            system=SYSTEM_FORMULARIO,
            messages=[{"role": "user", "content": mensaje}],
        )
    except anthropic.APIError as e:
        print(f"Fallo en la llamada al modelo {e}")
        errores.append("El agente no respondió. Intenta de nuevo en unos minutos.")
        return {"errores": errores}

    texto = "\n".join(b.text for b in respuesta.content if b.type == "text")
    try:
        campos = leer_json_modelo(texto).get("campos")
    except json.JSONDecodeError:
        errores.append("El agente devolvió una respuesta que no se pudo leer. Intenta de nuevo.")
        return {"errores": errores}
    if not isinstance(campos, list):
        errores.append("El agente devolvió una respuesta incompleta. Intenta de nuevo.")
        return {"errores": errores}
    return {"campos": campos}


def validar_formulario(estado: EstadoFormulario) -> EstadoFormulario:
    """Normaliza cada campo; lo que no se entiende pasa a 'no_sabe' (lo llena el usuario)."""
    if estado.get("errores"):
        return {}
    validos = []
    for c in estado.get("campos", []):
        if not isinstance(c, dict) or not str(c.get("pregunta") or "").strip():
            continue
        campo = {
            "pregunta": str(c["pregunta"]).strip(),
            "tipo": c.get("tipo"),
            "respuesta": str(c.get("respuesta") or "").strip(),
            "seguro": c.get("seguro") is True,
            "dato_personal": c.get("dato_personal"),
            "nota": str(c.get("nota") or "").strip(),
        }
        if campo["tipo"] == "dato_personal" and campo["dato_personal"] in DATOS_PERSONALES:
            campo["respuesta"] = ""  # el valor real lo pone Progent, nunca el modelo
        elif campo["tipo"] == "respuesta" and campo["respuesta"]:
            pass
        else:
            campo["tipo"] = "no_sabe"
            campo["respuesta"] = ""
            campo["nota"] = campo["nota"] or "El agente no supo cómo llenar este campo."
        validos.append(campo)
    if not validos:
        return {"errores": ["El agente no encontró preguntas en el formulario. Revisa el texto."]}
    return {"campos": validos}


def construir_grafo_formulario():
    g = StateGraph(EstadoFormulario)
    g.add_node("interpretar_formulario", interpretar_formulario)
    g.add_node("validar_formulario", validar_formulario)
    g.set_entry_point("interpretar_formulario")
    g.add_edge("interpretar_formulario", "validar_formulario")
    g.add_edge("validar_formulario", END)
    return g.compile()


grafo_formulario = construir_grafo_formulario()


def completar_formulario(formulario: str, perfil: dict) -> EstadoFormulario:
    """Punto de entrada usado por formularios.py."""
    return grafo_formulario.invoke({"formulario": formulario, "perfil": perfil, "errores": []})


# ==========================================================================
# Agente que sugiere mejoras a la hoja de vida (historia #24)
#
# Flujo:  sugerir_mejoras  ->  validar_mejoras  ->  END
#
# Recibe el perfil SIN datos personales (decisión 6) y las vacantes que le
# interesan al usuario. Nada se cambia en el perfil hasta que el usuario
# aplica una sugerencia (decisión 7); eso lo hace mejorasCv.py.
# ==========================================================================
from mejorasCv import separar_habilidades
from prompts import CAMPOS_MEJORA, SYSTEM_MEJORAS_CV, USER_MEJORAS_CV


def pedir_json_modelo(system, mensaje, max_tokens):
    """Llama al modelo y lee su JSON. Retorna (datos, None) o (None, mensaje de error)."""
    try:
        respuesta = cliente.messages.create(
            model=MODELO,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": mensaje}],
        )
    except anthropic.APIError as e:
        print(f"Fallo en la llamada al modelo {e}")
        return None, "El agente no respondió. Intenta de nuevo en unos minutos."
    texto = "\n".join(b.text for b in respuesta.content if b.type == "text")
    try:
        return leer_json_modelo(texto), None
    except json.JSONDecodeError:
        return None, "El agente devolvió una respuesta que no se pudo leer. Intenta de nuevo."


class EstadoMejoras(TypedDict, total=False):
    """Estado que viaja por el grafo de mejoras de la hoja de vida."""

    perfil: dict[str, Any]
    vacantes: list[dict[str, Any]]
    sugerencias: list[dict[str, Any]]
    errores: list[str]


def sugerir_mejoras(estado: EstadoMejoras) -> EstadoMejoras:
    errores = list(estado.get("errores", []))
    vacantes = [
        {
            "id_vacante": v["Id_vacante"],
            "cargo": v["Cargo"],
            "descripcion": v["Descripcion"],
            "requisitos": v["Requisitos"],
        }
        for v in estado["vacantes"]
    ]
    mensaje = USER_MEJORAS_CV.format(
        perfil=json.dumps(estado["perfil"], ensure_ascii=False, indent=2),
        vacantes=json.dumps(vacantes, ensure_ascii=False, indent=2),
    )
    datos, error = pedir_json_modelo(SYSTEM_MEJORAS_CV, mensaje, 3000)
    if error:
        return {"errores": errores + [error]}
    sugerencias = datos.get("sugerencias")
    if not isinstance(sugerencias, list):
        return {"errores": errores + ["El agente devolvió una respuesta incompleta. Intenta de nuevo."]}
    return {"sugerencias": sugerencias}


def validar_mejoras(estado: EstadoMejoras) -> EstadoMejoras:
    """Deja solo cambios aplicables: campo conocido, experiencia del usuario y texto nuevo."""
    if estado.get("errores"):
        return {}

    perfil = estado["perfil"]
    experiencias = {e["id_experiencia"]: e for e in perfil["experiencia"]}
    vacantes = {v["Id_vacante"]: v["Cargo"] for v in estado["vacantes"]}
    validas, vistas = [], set()
    for s in estado.get("sugerencias", []):
        if not isinstance(s, dict) or s.get("campo") not in CAMPOS_MEJORA:
            continue
        campo = s["campo"]
        propuesta = str(s.get("propuesta") or "").strip()
        motivo = str(s.get("motivo") or "").strip()
        if not propuesta or not motivo:
            continue

        if campo == "ocupacion":
            id_experiencia, actual = None, perfil.get("ocupacion") or ""
        else:
            try:
                id_experiencia = int(s.get("id_experiencia"))
            except (TypeError, ValueError):
                continue
            if id_experiencia not in experiencias:
                continue
            experiencia = experiencias[id_experiencia]
            actual = experiencia["funciones"] if campo == "funciones" else experiencia["habilidades"]

        if campo == "habilidades":
            # Solo las que todavía no tiene (sin importar mayúsculas).
            tiene = {h.lower() for h in separar_habilidades(actual)}
            nuevas = []
            for h in separar_habilidades(propuesta):
                if h.lower() not in tiene:
                    tiene.add(h.lower())
                    nuevas.append(h)
            if not nuevas:
                continue
            propuesta = ", ".join(nuevas)
        elif propuesta == (actual or "").strip():
            continue

        if (campo, id_experiencia) in vistas:
            continue
        vistas.add((campo, id_experiencia))

        ids_vacantes = []
        for v in s.get("vacantes") or []:
            try:
                v = int(v)
            except (TypeError, ValueError):
                continue
            if v in vacantes and v not in ids_vacantes:
                ids_vacantes.append(v)

        validas.append(
            {
                "campo": campo,
                "id_experiencia": id_experiencia,
                "actual": actual or "",
                "propuesta": propuesta,
                "motivo": motivo,
                "vacantes": [vacantes[v] for v in ids_vacantes],
                "seguro": s.get("seguro") is True,
            }
        )
    return {"sugerencias": validas[:6]}


def construir_grafo_mejoras():
    g = StateGraph(EstadoMejoras)
    g.add_node("sugerir_mejoras", sugerir_mejoras)
    g.add_node("validar_mejoras", validar_mejoras)
    g.set_entry_point("sugerir_mejoras")
    g.add_edge("sugerir_mejoras", "validar_mejoras")
    g.add_edge("validar_mejoras", END)
    return g.compile()


grafo_mejoras = construir_grafo_mejoras()


def sugerir_mejoras_cv(perfil, vacantes) -> EstadoMejoras:
    """Punto de entrada usado por mejorasCv.py."""
    return grafo_mejoras.invoke({"perfil": perfil, "vacantes": vacantes, "errores": []})


if __name__ == "__main__":
    import sys

    with open(sys.argv[1], "rb") as f:
        resultado = procesar_cv(f.read())
    print(json.dumps(resultado.get("perfil", {}), indent=2, ensure_ascii=False))
    if resultado.get("errores"):
        print("\nERRORES:", resultado["errores"])
