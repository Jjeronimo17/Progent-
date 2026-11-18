"""Mis postulaciones: estado (#21, #22, #23), entrevista (#28), carta (#18),
formulario (#19), hoja de vida asociada (#20) y prioridades (#29)."""
import datetime as dt

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel

from nucleo import con_datos, con_mensaje, correo_actual, descarga, respuesta

router = APIRouter(prefix="/api", tags=["postulaciones"])


@router.get("/postulaciones")
def listar(correo: str = Depends(correo_actual)):
    from postulaciones import consultarPostulaciones

    return con_datos(consultarPostulaciones(correo))


class Estado(BaseModel):
    estado: str


@router.put("/postulaciones/{id_postulacion}/estado")
def cambiar_estado(id_postulacion: int, cuerpo: Estado, correo: str = Depends(correo_actual)):
    from postulaciones import cambiarEstado

    return con_mensaje(cambiarEstado(correo, id_postulacion, cuerpo.estado))


@router.post("/postulaciones/{id_postulacion}/deshacer")
def deshacer(id_postulacion: int, correo: str = Depends(correo_actual)):
    from postulaciones import deshacerUltimoCambio

    return con_mensaje(deshacerUltimoCambio(correo, id_postulacion))


# --- Entrevista (#28) --------------------------------------------------------
class Entrevista(BaseModel):
    fecha: dt.datetime  # ISO 8601, hora local (ej.: 2026-11-25T15:30)


@router.put("/postulaciones/{id_postulacion}/entrevista")
def guardar_entrevista(id_postulacion: int, cuerpo: Entrevista, correo: str = Depends(correo_actual)):
    from entrevistas import guardarEntrevista

    fecha = cuerpo.fecha.replace(tzinfo=None, second=0, microsecond=0)
    return con_mensaje(guardarEntrevista(correo, id_postulacion, fecha))


@router.delete("/postulaciones/{id_postulacion}/entrevista")
def quitar_entrevista(id_postulacion: int, correo: str = Depends(correo_actual)):
    from entrevistas import quitarEntrevista

    return con_mensaje(quitarEntrevista(correo, id_postulacion))


@router.get("/recordatorios")
def recordatorios(correo: str = Depends(correo_actual)):
    from entrevistas import consultarRecordatorios

    return con_datos(consultarRecordatorios(correo))


# --- Carta de presentación (#18) -------------------------------------------
@router.get("/postulaciones/{id_postulacion}/carta")
def ver_carta(id_postulacion: int, correo: str = Depends(correo_actual)):
    from documentos import consultarCarta

    return con_datos(consultarCarta(correo, id_postulacion))


@router.get("/postulaciones/{id_postulacion}/carta/archivo")
def descargar_carta(id_postulacion: int, correo: str = Depends(correo_actual)):
    from documentos import consultarCarta

    exito, carta = consultarCarta(correo, id_postulacion)
    if not exito or not carta:
        return respuesta(False, carta if isinstance(carta, str) else "Esta postulación no tiene carta.")
    datos = next(v for v in carta.values() if isinstance(v, (bytes, bytearray)))
    nombre = next((v for k, v in carta.items() if "nombre" in k.lower()), "carta")
    tipo = next((v for k, v in carta.items() if k.lower() == "tipo"), None)
    return descarga(datos, nombre, tipo)


@router.put("/postulaciones/{id_postulacion}/carta")
async def subir_carta(id_postulacion: int, archivo: UploadFile = File(...), correo: str = Depends(correo_actual)):
    """PDF o .docx de 2 MB como máximo (lo valida documentos.validarDocumento)."""
    from documentos import guardarCarta

    return con_mensaje(guardarCarta(correo, id_postulacion, archivo.filename, await archivo.read()))


# --- Formulario de la vacante (#19) ----------------------------------------
@router.post("/postulaciones/{id_postulacion}/formulario/leer")
async def leer_formulario(id_postulacion: int, archivo: UploadFile = File(...), correo: str = Depends(correo_actual)):
    """Saca el texto de un formulario en PDF o Word (el usuario también puede pegarlo)."""
    from formularios import leerFormulario

    return con_datos(leerFormulario(archivo.filename, await archivo.read()))


class TextoFormulario(BaseModel):
    texto: str = ""


@router.post("/postulaciones/{id_postulacion}/formulario/generar")
def generar_respuestas(id_postulacion: int, cuerpo: TextoFormulario, correo: str = Depends(correo_actual)):
    """El agente propone; nada se guarda hasta que el usuario confirma (decisión 7)."""
    from formularios import generarRespuestas

    return con_datos(generarRespuestas(correo, id_postulacion, cuerpo.texto))


class Respuestas(BaseModel):
    respuestas: list[tuple[str, str]]


@router.put("/postulaciones/{id_postulacion}/formulario")
def guardar_respuestas(id_postulacion: int, cuerpo: Respuestas, correo: str = Depends(correo_actual)):
    from formularios import guardarRespuestas

    return con_mensaje(guardarRespuestas(correo, id_postulacion, [tuple(r) for r in cuerpo.respuestas]))


@router.get("/postulaciones/{id_postulacion}/formulario")
def ver_respuestas(id_postulacion: int, correo: str = Depends(correo_actual)):
    from formularios import consultarRespuestas

    return con_datos(consultarRespuestas(correo, id_postulacion))


# --- Prioridades (#29) -------------------------------------------------------
@router.post("/prioridades")
def prioridades(correo: str = Depends(correo_actual)):
    """Con 0 o 1 procesos activos no se llama al agente (lo decide la lógica)."""
    from prioridades import generarPrioridades

    exito, datos = generarPrioridades(correo)
    if exito:
        datos = {**datos, "procesos": list(datos["procesos"].values())}
    return con_datos((exito, datos))
