"""Mi perfil: datos manuales, hoja de vida (#5), importación (#4, #6), mejoras (#24) y CV (#7)."""
import datetime as dt
import unicodedata

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

import columnas
from nucleo import con_datos, con_mensaje, correo_actual, descarga, respuesta

router = APIRouter(prefix="/api", tags=["perfil"])

TIPO_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _texto_o_none(valor):
    valor = (valor or "").strip()
    return valor or None


def _faltan(campos: dict) -> str | None:
    vacios = [nombre for nombre, valor in campos.items() if not str(valor or "").strip()]
    if vacios:
        return "Completa los campos obligatorios: " + ", ".join(vacios) + "."
    return None


# ---------------------------------------------------------------------------
# Perfil manual (PerfilFront)
# ---------------------------------------------------------------------------
@router.get("/perfil")
def ver_perfil(correo: str = Depends(correo_actual)):
    from datosUsuario import consultarArchivo, consultarDatos, consultarEducacion, consultarExperiencia

    exito, datos = consultarDatos(correo)
    if not exito:
        return respuesta(False, datos)
    exito, experiencia = consultarExperiencia(correo)
    if not exito:
        return respuesta(False, experiencia)
    exito, educacion = consultarEducacion(correo)
    if not exito:
        return respuesta(False, educacion)
    exito, archivo = consultarArchivo(correo)
    hoja = None
    if exito and archivo:
        hoja = {"nombre": archivo[1], "tipo": archivo[2]}
    return respuesta(
        True,
        None,
        {
            "datos": columnas.fila("informacion_usuarios", datos),
            "experiencia": columnas.filas("Experiencia", experiencia),
            "educacion": columnas.filas("Educacion", educacion),
            "hoja_de_vida": hoja,
        },
    )


class DatosBasicos(BaseModel):
    nombre: str = ""
    edad: int | None = None
    telefono: str | None = None
    correo_contacto: str = ""
    ubicacion: str = ""
    ocupacion: str = ""


@router.post("/perfil/datos")
def guardar_datos(cuerpo: DatosBasicos, correo: str = Depends(correo_actual)):
    from datosUsuario import añadirDatos

    falta = _faltan(
        {
            "Nombre completo": cuerpo.nombre,
            "Correo de contacto": cuerpo.correo_contacto,
            "Ubicación": cuerpo.ubicacion,
            "Ocupación": cuerpo.ocupacion,
        }
    )
    if falta:
        return respuesta(False, falta)
    if "@" not in cuerpo.correo_contacto:
        return respuesta(False, "Escribe un correo de contacto válido.")
    return con_mensaje(
        añadirDatos(
            correo,
            cuerpo.nombre.strip(),
            cuerpo.edad,
            _texto_o_none(cuerpo.telefono),
            cuerpo.correo_contacto.strip(),
            cuerpo.ubicacion.strip(),
            cuerpo.ocupacion.strip(),
        )
    )


@router.put("/perfil/datos")
def actualizar_datos(cuerpo: DatosBasicos, correo: str = Depends(correo_actual)):
    from datosUsuario import actualizarPerfil

    return con_mensaje(
        actualizarPerfil(
            correo,
            cuerpo.nombre.strip(),
            cuerpo.edad,
            _texto_o_none(cuerpo.telefono),
            cuerpo.correo_contacto.strip(),
            cuerpo.ubicacion.strip(),
            cuerpo.ocupacion.strip(),
        )
    )


class Experiencia(BaseModel):
    empresa: str = ""
    cargo: str = ""
    fecha_inicio: dt.date | None = None
    fecha_fin: dt.date | None = None
    funciones: str = ""
    habilidades: str = ""
    logros: str | None = None
    ubicacion: str | None = None
    modalidad: str | None = None  # Hibrido | Presencial | Virtual | None


@router.post("/perfil/experiencia")
def agregar_experiencia(cuerpo: Experiencia, correo: str = Depends(correo_actual)):
    from datosUsuario import añadirExperiencia

    falta = _faltan(
        {
            "Empresa": cuerpo.empresa,
            "Cargo": cuerpo.cargo,
            "Fecha de inicio": cuerpo.fecha_inicio,
            "Descripción de funciones": cuerpo.funciones,
            "Habilidades": cuerpo.habilidades,
        }
    )
    if falta:
        return respuesta(False, falta)
    modalidad = cuerpo.modalidad if cuerpo.modalidad in ("Hibrido", "Presencial", "Virtual") else None
    return con_mensaje(
        añadirExperiencia(
            correo,
            cuerpo.empresa.strip(),
            None,
            None,
            cuerpo.cargo.strip(),
            None,
            cuerpo.fecha_inicio,
            cuerpo.funciones.strip(),
            _texto_o_none(cuerpo.logros),
            cuerpo.habilidades.strip(),
            _texto_o_none(cuerpo.ubicacion),
            None,
            modalidad,
            fecha_finalizacion=cuerpo.fecha_fin,
        )
    )


class Educacion(BaseModel):
    institucion: str = ""
    titulo: str = ""
    nivel: str | None = None
    campo: str | None = None
    fecha_inicio: dt.date | None = None
    fecha_fin: dt.date | None = None
    estado: str = "Cursando"
    logros: str | None = None


@router.post("/perfil/educacion")
def agregar_educacion(cuerpo: Educacion, correo: str = Depends(correo_actual)):
    from datosUsuario import añadirEducacion

    falta = _faltan(
        {"Institución": cuerpo.institucion, "Título o carrera": cuerpo.titulo, "Fecha de inicio": cuerpo.fecha_inicio}
    )
    if falta:
        return respuesta(False, falta)
    return con_mensaje(
        añadirEducacion(
            correo,
            cuerpo.institucion.strip(),
            None,
            cuerpo.titulo.strip(),
            _texto_o_none(cuerpo.nivel),
            _texto_o_none(cuerpo.campo),
            cuerpo.fecha_inicio,
            cuerpo.estado,
            _texto_o_none(cuerpo.logros),
            fecha_final=cuerpo.fecha_fin,
        )
    )


# ---------------------------------------------------------------------------
# Hoja de vida del perfil (#5)
# ---------------------------------------------------------------------------
@router.get("/perfil/hoja-de-vida")
def ver_hoja(correo: str = Depends(correo_actual)):
    from datosUsuario import consultarArchivo

    exito, archivo = consultarArchivo(correo)
    if not exito:
        return respuesta(False, archivo)
    if archivo is None:
        return respuesta(True, None, None)
    return respuesta(True, None, {"nombre": archivo[1], "tipo": archivo[2]})


@router.get("/perfil/hoja-de-vida/archivo")
def descargar_hoja(correo: str = Depends(correo_actual)):
    from datosUsuario import consultarArchivo

    exito, archivo = consultarArchivo(correo)
    if not exito or archivo is None:
        return respuesta(False, archivo if isinstance(archivo, str) else "Todavía no tienes una hoja de vida guardada en tu perfil.")
    return descarga(archivo[3], archivo[1], archivo[2])


@router.put("/perfil/hoja-de-vida")
async def guardar_hoja(archivo: UploadFile = File(...), correo: str = Depends(correo_actual)):
    """Guarda o reemplaza la hoja de vida («Guardar en mi perfil»)."""
    from documentos import guardarHojaDeVida

    return con_mensaje(guardarHojaDeVida(correo, archivo.filename, await archivo.read()))


@router.post("/perfil/hoja-de-vida")
async def cargar_hoja_para_postular(archivo: UploadFile = File(...), correo: str = Depends(correo_actual)):
    """Carga la hoja de vida solo si aún no hay una (la usa «Postularme» en Vacantes)."""
    from documentos import guardarCvPerfil

    return con_mensaje(guardarCvPerfil(correo, archivo.filename, await archivo.read()))


# ---------------------------------------------------------------------------
# Importar el perfil con el agente: hoja de vida (#6) o PDF de LinkedIn (#4)
# ---------------------------------------------------------------------------
@router.post("/importacion/extraer")
async def extraer(
    archivo: UploadFile = File(...),
    origen: str = Form("cv"),
    correo: str = Depends(correo_actual),
):
    """Devuelve el borrador para revisar. NO guarda nada (decisión 7).

    datos = {"sin_texto": bool, "borrador": {...} | None}
    """
    from cargarLinkedin import extraerPerfilLinkedin
    from importarPerfil import extraerPerfil

    contenido = await archivo.read()
    if origen == "linkedin":
        return con_datos(extraerPerfilLinkedin(correo, archivo.filename, contenido))
    return con_datos(extraerPerfil(correo, archivo.filename, contenido, "cv"))


class Importacion(BaseModel):
    borrador: dict
    revise: bool = False


@router.post("/importacion/confirmar")
def confirmar_importacion(cuerpo: Importacion, correo: str = Depends(correo_actual)):
    from importarPerfil import guardarPerfilImportado

    if cuerpo.borrador.get("dudosos") and not cuerpo.revise:
        return respuesta(False, "Confirma que revisaste los datos que el agente marcó como dudosos.")
    return con_mensaje(guardarPerfilImportado(correo, cuerpo.borrador))


# ---------------------------------------------------------------------------
# Mejorar la hoja de vida (#24)
# ---------------------------------------------------------------------------
@router.get("/mejoras/vacantes-interes")
def vacantes_interes(correo: str = Depends(correo_actual)):
    from mejorasCv import consultarVacantesInteres

    return con_datos(consultarVacantesInteres(correo))


@router.post("/mejoras/sugerencias")
def sugerencias(correo: str = Depends(correo_actual)):
    """Lo que propone el agente vive en el cliente hasta que el usuario lo aplica."""
    from mejorasCv import generarSugerencias

    return con_datos(generarSugerencias(correo))


class Sugerencia(BaseModel):
    campo: str
    id_experiencia: int | None = None
    texto: str


@router.post("/mejoras/aplicar")
def aplicar(cuerpo: Sugerencia, correo: str = Depends(correo_actual)):
    from mejorasCv import aplicarSugerencia

    return con_mensaje(aplicarSugerencia(correo, cuerpo.campo, cuerpo.id_experiencia, cuerpo.texto))


# ---------------------------------------------------------------------------
# Generar el CV (#7)
# ---------------------------------------------------------------------------
def _nombre_cv(cv):
    # El mismo nombre que GenerarCvFront: sin tildes, «CV <nombre>.docx».
    nombre = unicodedata.normalize("NFKD", cv["nombre"]).encode("ascii", "ignore").decode()
    return f"CV {nombre}.docx"


class CV(BaseModel):
    cv: dict


@router.post("/cv/borrador")
def borrador_cv(correo: str = Depends(correo_actual)):
    """datos = {"cv": {...} | None, "faltantes": [...]}. No guarda nada."""
    from graph import generarBorradorCV

    return con_datos(generarBorradorCV(correo))


@router.post("/cv/documento")
def documento_cv(cuerpo: CV, correo: str = Depends(correo_actual)):
    """El .docx del borrador tal como el usuario lo editó (solo descarga)."""
    from graph import generarDocumentoCV

    exito, documento = generarDocumentoCV(cuerpo.cv)
    if not exito:
        return respuesta(False, documento)
    return descarga(documento, _nombre_cv(cuerpo.cv), TIPO_DOCX)


@router.post("/cv/confirmar")
def confirmar_cv(cuerpo: CV, correo: str = Depends(correo_actual)):
    """«Confirmar CV»: queda como la hoja de vida del perfil (decisión 7)."""
    from documentos import guardarCvGenerado
    from graph import generarDocumentoCV

    exito, documento = generarDocumentoCV(cuerpo.cv)
    if not exito:
        return respuesta(False, documento)
    return con_mensaje(guardarCvGenerado(correo, _nombre_cv(cuerpo.cv), documento))
