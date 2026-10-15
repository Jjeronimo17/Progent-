"""Grafo del agente de extraccion de perfil (Progent - prueba de concepto).

Flujo:  leer_pdf  ->  extraer  ->  validar  ->  END

El grafo es intencionalmente pequeño: la prueba de concepto busca demostrar que el
ambiente funciona de punta a punta, no cubrir todos los casos.
"""

import io
import json
import os
from datetime import date, datetime
from typing import Any, Literal, TypedDict

import anthropic
import datosUsuario
from docx import Document
from docx.shared import Pt, RGBColor
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from prompts import (
    SYSTEM_EXTRACCION,
    SYSTEM_EXTRACCION_LINKEDIN,
    SYSTEM_REDACCION_CV,
    USER_EXTRACCION,
    USER_REDACCION_CV,
)
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
    secciones_faltantes: list[str]
    redaccion: dict[str, Any]
    cv: dict[str, Any]


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
        generales = dict(zip(columnas_generales, informacion_general_perfil or ()))
        experiencias = [dict(zip(columnas_exp, f)) for f in informacion_experiencia]
        estudios = [dict(zip(columnas_edu, f)) for f in informacion_educacion]
        perfil = {
            "generales": generales,
            "experiencia": experiencias,
            "educacion": estudios,
        }
        return {"perfil": perfil}


def verificarPerfilCompleto(estado: EstadoPerfil) -> EstadoPerfil:
    if estado.get("errores"):
        return {}

    generales = estado["perfil"]["generales"]
    secciones_faltantes = []
    if not estado["perfil"]["experiencia"]:
        secciones_faltantes.append("Experiencia no encontrada")
    if not estado["perfil"]["educacion"]:
        secciones_faltantes.append("Educacion no encontrada")
    if not generales.get("Nombre"):
        secciones_faltantes.append("Nombre no encontrado")
    if not generales.get("Edad"):
        secciones_faltantes.append("Edad no encontrada")
    if not generales.get("Telefono"):
        secciones_faltantes.append("Telefono no encontrado")
    if not generales.get("Correo_contacto"):
        secciones_faltantes.append("Correo de contacto no encontrado")
    if not generales.get("Ubicacion"):
        secciones_faltantes.append("Ubicacion no encontrada")
    if not generales.get("Ocupacion"):
        secciones_faltantes.append("Ocupacion no encontrada")

    return {"secciones_faltantes": secciones_faltantes}


def rutaVerificacion(estado: EstadoPerfil) -> Literal["redactar", "terminar"]:
    if estado.get("errores") or estado.get("secciones_faltantes"):
        return "terminar"
    return "redactar"


MESES = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.",
         "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]


def _a_fecha(valor):
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str) and valor.strip():
        try:
            return datetime.strptime(valor.strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _periodo(inicio, fin, texto_actual="actualidad"):
    i, f = _a_fecha(inicio), _a_fecha(fin)
    if i is None:
        return ""
    texto_inicio = f"{MESES[i.month - 1]} {i.year}"
    texto_fin = f"{MESES[f.month - 1]} {f.year}" if f else texto_actual
    return f"{texto_inicio} – {texto_fin}"


def _texto(valor):
    return str(valor).strip() if valor is not None else ""


def _perfilParaModelo(perfil):
    """Copia del perfil SIN datos personales ni identificadores internos."""
    experiencias = []
    for i, e in enumerate(perfil["experiencia"]):
        experiencias.append({
            "indice": i,
            "cargo": e.get("Titulo_puesto"),
            "empresa": e.get("Nombre_empresa"),
            "sector": e.get("Sector_industria"),
            "nivel": e.get("Nivel_seniority"),
            "fecha_inicio": e.get("Fecha_inicio"),
            "fecha_fin": e.get("Fecha_finalizacion"),
            "funciones": e.get("Descripcion_funciones"),
            "logros": e.get("Logros"),
            "habilidades": e.get("Habilidades"),
            "modalidad": e.get("Modalidad_trabajo"),
        })
    estudios = [
        {
            "titulo": e.get("Titulo_Carrera_grado"),
            "institucion": e.get("Institucion_educativa"),
            "nivel": e.get("Nivel_educacion"),
            "campo": e.get("Campo_Estudio"),
            "estado": e.get("Estado_Estudio"),
            "logros": e.get("Logros"),
        }
        for e in perfil["educacion"]
    ]
    return {
        "ocupacion": perfil["generales"].get("Ocupacion"),
        "experiencia": experiencias,
        "educacion": estudios,
    }


def redactarCV(estado: EstadoPerfil) -> EstadoPerfil:
    errores = list(estado.get("errores", []))
    perfil_limpio = _perfilParaModelo(estado["perfil"])

    respuesta = cliente.messages.create(
        model=MODELO,
        max_tokens=3000,
        system=SYSTEM_REDACCION_CV,
        messages=[
            {
                "role": "user",
                "content": USER_REDACCION_CV.format(
                    perfil=json.dumps(perfil_limpio, ensure_ascii=False, indent=2, default=str)
                ),
            },
        ],
    )

    bloques = [b.text for b in respuesta.content if b.type == "text"]
    if not bloques:
        errores.append("El modelo no devolvio texto")
        return {"errores": errores}
    crudo = "\n".join(bloques).strip()

    inicio, fin = crudo.find("{"), crudo.rfind("}")
    if inicio != -1 and fin != -1:
        crudo = crudo[inicio : fin + 1]

    try:
        redaccion = json.loads(crudo)
    except json.JSONDecodeError as e:
        errores.append(f"El modelo no devolvio JSON valido: {e}")
        return {"errores": errores}

    return {"redaccion": redaccion}


def armarCV(estado: EstadoPerfil) -> EstadoPerfil:
    if estado.get("errores"):
        return {}

    errores = list(estado.get("errores", []))
    perfil = estado["perfil"]
    generales = perfil["generales"]
    redaccion = estado.get("redaccion") or {}

    if not isinstance(redaccion.get("experiencias", []), list):
        errores.append("La redaccion no trae la lista de experiencias")
        return {"errores": errores}

    logros_por_indice = {}
    for item in redaccion.get("experiencias", []):
        if isinstance(item, dict) and isinstance(item.get("indice"), int):
            logros_por_indice[item["indice"]] = [
                _texto(l) for l in item.get("logros", []) if _texto(l)
            ]

    dudosas = [_texto(s) for s in redaccion.get("secciones_dudosas", []) if _texto(s)]

    experiencia = []
    for i, e in enumerate(perfil["experiencia"]):
        logros = logros_por_indice.get(i, [])
        if not logros and f"experiencia {i + 1}" not in dudosas:
            dudosas.append(f"experiencia {i + 1}")
        experiencia.append({
            "cargo": _texto(e.get("Titulo_puesto")),
            "empresa": _texto(e.get("Nombre_empresa")),
            "ubicacion": _texto(e.get("Ubicacion_empresa")),
            "periodo": _periodo(e.get("Fecha_inicio"), e.get("Fecha_finalizacion")),
            "logros": logros,
        })

    educacion = [
        {
            "titulo": _texto(e.get("Titulo_Carrera_grado")),
            "institucion": _texto(e.get("Institucion_educativa")),
            "periodo": _periodo(e.get("Fecha_inicio"), e.get("Fecha_final"), "en curso"),
            "estado": _texto(e.get("Estado_Estudio")),
        }
        for e in perfil["educacion"]
    ]

    resumen = _texto(redaccion.get("resumen"))
    if not resumen and "resumen" not in dudosas:
        dudosas.append("resumen")

    cv = {
        "nombre": _texto(generales.get("Nombre")),
        "titular": _texto(generales.get("Ocupacion")),
        "contacto": {
            "correo": _texto(generales.get("Correo_contacto")),
            "telefono": _texto(generales.get("Telefono")),
            "ubicacion": _texto(generales.get("Ubicacion")),
        },
        "resumen": resumen,
        "experiencia": experiencia,
        "educacion": educacion,
        "habilidades": [_texto(h) for h in redaccion.get("habilidades", []) if _texto(h)],
        "secciones_dudosas": dudosas,
    }
    return {"cv": cv}


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


def construir_grafo_cv():
    g = StateGraph(EstadoPerfil)
    g.add_node("cargarPerfil", cargarPerfil)
    g.add_node("verificarPerfilCompleto", verificarPerfilCompleto)
    g.add_node("redactarCV", redactarCV)
    g.add_node("armarCV", armarCV)

    g.set_entry_point("cargarPerfil")
    g.add_edge("cargarPerfil", "verificarPerfilCompleto")
    g.add_conditional_edges(
        "verificarPerfilCompleto",
        rutaVerificacion,
        {"redactar": "redactarCV", "terminar": END},
    )
    g.add_edge("redactarCV", "armarCV")
    g.add_edge("armarCV", END)

    return g.compile()


grafo_cv = construir_grafo_cv()


def generarBorradorCV(correo):
    try:
        estado = grafo_cv.invoke({"correo": correo, "errores": []})
    except Exception as e:
        print(f"Error generando el CV {e}")
        return False, "No se pudo generar el CV, intenta de nuevo"

    if estado.get("errores"):
        print("Errores del grafo:", estado["errores"])
        return False, "No se pudo generar el CV, intenta de nuevo"

    secciones_faltantes = estado.get("secciones_faltantes") or []
    if secciones_faltantes:
        return False, "Tu perfil esta incompleto: " + ", ".join(secciones_faltantes)

    return True, estado["cv"]


def generarDocumentoCV(cv):
    if not isinstance(cv, dict) or not _texto(cv.get("nombre")):
        return False, "El CV no tiene nombre, no se puede generar el documento"

    try:
        doc = Document()
        azul = RGBColor(0x1F, 0x3A, 0x5F)
        gris = RGBColor(0x55, 0x55, 0x55)

        def linea(texto, tam=10.5, negrita=False, color=None, despues=2):
            p = doc.add_paragraph()
            r = p.add_run(texto)
            r.font.size = Pt(tam)
            r.bold = negrita
            if color:
                r.font.color.rgb = color
            p.paragraph_format.space_after = Pt(despues)
            return p

        def seccion(titulo):
            p = linea(titulo.upper(), tam=12, negrita=True, color=azul, despues=4)
            p.paragraph_format.space_before = Pt(12)

        linea(cv["nombre"], tam=22, negrita=True, color=azul, despues=0)
        if _texto(cv.get("titular")):
            linea(cv["titular"], tam=12, color=gris)
        contacto = cv.get("contacto") or {}
        datos = [_texto(contacto.get(k)) for k in ("correo", "telefono", "ubicacion")]
        datos = [d for d in datos if d]
        if datos:
            linea("  ·  ".join(datos), tam=10, color=gris)

        if _texto(cv.get("resumen")):
            seccion("Perfil profesional")
            linea(cv["resumen"])

        if cv.get("experiencia"):
            seccion("Experiencia")
            for e in cv["experiencia"]:
                encabezado = " — ".join(
                    x for x in (_texto(e.get("cargo")), _texto(e.get("empresa"))) if x
                )
                linea(encabezado, tam=11, negrita=True, despues=0)
                detalle = " · ".join(
                    x for x in (_texto(e.get("periodo")), _texto(e.get("ubicacion"))) if x
                )
                if detalle:
                    linea(detalle, tam=9.5, color=gris)
                for logro in e.get("logros") or []:
                    if _texto(logro):
                        p = doc.add_paragraph(_texto(logro), style="List Bullet")
                        p.runs[0].font.size = Pt(10.5)

        if cv.get("educacion"):
            seccion("Educación")
            for e in cv["educacion"]:
                linea(_texto(e.get("titulo")), tam=11, negrita=True, despues=0)
                detalle = " · ".join(
                    x for x in (_texto(e.get("institucion")), _texto(e.get("periodo"))) if x
                )
                if detalle:
                    linea(detalle, tam=10, color=gris)

        if cv.get("habilidades"):
            seccion("Habilidades")
            linea(", ".join(_texto(h) for h in cv["habilidades"] if _texto(h)))

        salida = io.BytesIO()
        doc.save(salida)
        return True, salida.getvalue()

    except Exception as e:
        print(f"Error armando el documento {e}")
        return False, "No se pudo generar el documento del CV"


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
