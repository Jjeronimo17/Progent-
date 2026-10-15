"""Grafo del agente de extraccion de perfil (Progent - prueba de concepto).

Flujo:  leer_pdf  ->  extraer  ->  validar  ->  END

El grafo es intencionalmente pequeño: la prueba de concepto busca demostrar que el
ambiente funciona de punta a punta, no cubrir todos los casos.
"""

import io
import json
import os
from typing import Any, Literal, TypedDict

import anthropic
import datosUsuario
from docx import Document
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from prompts import SYSTEM_EXTRACCION, SYSTEM_EXTRACCION_LINKEDIN, USER_EXTRACCION
from pypdf import PdfReader

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
    correo: str
    secciones_faltantes: [str]


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


def cargarPerfil(estado: EstadoPerfil) -> EstadoPerfil:
    booleano_info_general, informacion_general_perfil = datosUsuario.consultarDatos(
        estado["correo"]
    )
    booleano_experiencia, informacion_experiencia = datosUsuario.consultarExperiencia(
        estado["correo"]
    )
    booleano_educacion, informacion_educacion = datosUsuario.consultarEducacion(
        estado["correo"]
    )
    if not booleano_info_general:
        errores = list(estado.get("errores", []))
        errores.append("No se pudo acceder a los datos del perfil")
        return {"errores": errores}
    elif not booleano_experiencia:
        errores = list(estado.get("errores", []))
        errores.append("No se pudo acceder a la experiencia del perfil")
        return {"errores": errores}
    elif not booleano_educacion:
        errores = list(estado.get("errores", []))
        errores.append("No se pudo acceder a la educacion del perfil")
        return {"errores": errores}
    else:
        columnas_generales = [
            "Correos",
            "Nombre",
            "Edad",
            "Telefono",
            "Correo_contacto",
            "Ubicacion",
            "Ocupacion",
        ]
        columnas_exp = [
            "ID",
            "Correos_experiencia",
            "Nombre_empresa",
            "Sector_industria",
            "Tamaño_empresa",
            "Titulo_puesto",
            "Nivel_seniority",
            "Fecha_inicio",
            "Fecha_finalizacion",
            "Descripcion_funciones",
            "Logros",
            "Habilidades",
            "Ubicacion_empresa",
            "Tipo_contrato",
            "Modalidad_trabajo",
        ]
        columnas_edu = [
            "Id_educacion",
            "Correos_educacion",
            "Institucion_educativa",
            "Tipo_institucion",
            "Titulo_Carrera_grado",
            "Nivel_educacion",
            "Campo_Estudio",
            "Fecha_inicio",
            "Fecha_final",
            "Estado_Estudio",
            "Logros",
        ]
        generales = dict(zip(columnas_generales, informacion_general_perfil))
        experiencias = [dict(zip(columnas_exp, f)) for f in informacion_experiencia]
        estudios = [dict(zip(columnas_edu, f)) for f in informacion_educacion]
        perfil = {
            "generales": generales,
            "experiencia": experiencias,
            "educacion": estudios,
        }
        return {"perfil": perfil}


def verificarPerfilCompleto(estado: EstadoPerfil) -> EstadoPerfil:
    if not estado["perfil"]["experiencia"]:
        estado["secciones_faltantes"].append("Experiencia no encontrada")
    if not estado["perfil"]["educacion"]:
        estado["secciones_faltantes"].append("Educacion no encontrada")
    if not estado["perfil"]["generales"]["Nombre"]:
        estado["secciones_faltantes"].append("Nombre no encontrado")
    if not estado["perfil"]["generales"]["Edad"]:
        estado["secciones_faltantes"].append("Edad no encontrada")
    if not estado["perfil"]["generales"]["Telefono"]:
        estado["secciones_faltantes"].append("Telefono no encontrado")
    if not estado["perfil"]["generales"]["Correo_contacto"]:
        estado["secciones_faltantes"].append("Correo de contacto no encontrado")
    if not estado["perfil"]["generales"]["Ubicacion"]:
        estado["secciones_faltantes"].append("Ubicacion no encontrada")
    if not estado["perfil"]["generales"]["Ocupacion"]:
        estado["secciones_faltantes"].append("Ocupacion no encontrada")


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


if __name__ == "__main__":
    import sys

    with open(sys.argv[1], "rb") as f:
        resultado = procesar_cv(f.read())
    print(json.dumps(resultado.get("perfil", {}), indent=2, ensure_ascii=False))
    if resultado.get("errores"):
        print("\nERRORES:", resultado["errores"])
