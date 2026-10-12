"""Grafo del agente de extraccion de perfil (Progent - prueba de concepto).

Flujo:  leer_pdf  ->  extraer  ->  validar  ->  END

El grafo es intencionalmente pequeño: la prueba de concepto busca demostrar que el
ambiente funciona de punta a punta, no cubrir todos los casos.
"""

import io
import json
import os
from typing import Any, TypedDict

import anthropic
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from pypdf import PdfReader

from prompts import SYSTEM_EXTRACCION, USER_EXTRACCION

load_dotenv()

MODELO = os.getenv("MODELO", "claude-haiku-4-5-20251001")
cliente = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno


class EstadoPerfil(TypedDict, total=False):
    """Estado que viaja por el grafo."""

    pdf_bytes: bytes
    texto: str
    perfil: dict[str, Any]
    errores: list[str]


# --------------------------------------------------------------------------
# Nodo 1: sacar el texto del PDF
# --------------------------------------------------------------------------
def leer_pdf(estado: EstadoPerfil) -> EstadoPerfil:
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

    g.set_entry_point("leer_pdf")
    g.add_edge("leer_pdf", "extraer")
    g.add_edge("extraer", "validar")
    g.add_edge("validar", END)

    return g.compile()


grafo = construir_grafo()


def procesar_cv(pdf_bytes: bytes) -> EstadoPerfil:
    """Punto de entrada usado por la interfaz."""
    return grafo.invoke({"pdf_bytes": pdf_bytes, "errores": []})


if __name__ == "__main__":
    import sys

    with open(sys.argv[1], "rb") as f:
        resultado = procesar_cv(f.read())
    print(json.dumps(resultado.get("perfil", {}), indent=2, ensure_ascii=False))
    if resultado.get("errores"):
        print("\nERRORES:", resultado["errores"])
