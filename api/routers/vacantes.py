"""Vacantes, compatibilidad (#26), guardadas (#16), alertas y notificaciones (#17), recomendaciones (#11, #25, #27)."""
import hashlib

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from nucleo import con_datos, con_mensaje, correo_actual, respuesta

router = APIRouter(prefix="/api", tags=["vacantes"])


# ---------------------------------------------------------------------------
# Vacantes
# ---------------------------------------------------------------------------
@router.get("/vacantes")
def listar(
    palabra_clave: str | None = None,
    ubicacion: str | None = None,
    salario_minimo: int | None = None,
    modalidad: str | None = None,
    correo: str = Depends(correo_actual),
):
    from vacantes import consultarVacantes

    return con_datos(
        consultarVacantes(
            (palabra_clave or "").strip() or None,
            ubicacion or None,
            salario_minimo or None,
            modalidad or None,
        )
    )


@router.get("/vacantes/ubicaciones")
def ubicaciones(correo: str = Depends(correo_actual)):
    from vacantes import consultarUbicaciones

    return con_datos(consultarUbicaciones())


@router.get("/vacantes/{id_vacante}")
def detalle(id_vacante: int, correo: str = Depends(correo_actual)):
    """La vacante, si el usuario la guardó y su postulación (si existe)."""
    from guardadas import estaGuardada
    from postulaciones import consultarPostulacion
    from vacantes import consultarVacante

    exito, vacante = consultarVacante(id_vacante)
    if not exito:
        return respuesta(False, vacante)
    if vacante is None:
        return respuesta(False, "Esta vacante ya no existe.")
    exito_g, guardada = estaGuardada(correo, id_vacante)
    exito_p, postulacion = consultarPostulacion(correo, id_vacante)
    return respuesta(
        True,
        None,
        {
            "vacante": vacante,
            "guardada": guardada if exito_g else None,
            "postulacion": postulacion if exito_p else None,
            "avisos": [m for ok, m in ((exito_g, guardada), (exito_p, postulacion)) if not ok],
        },
    )


@router.put("/vacantes/{id_vacante}/guardada")
def guardar(id_vacante: int, correo: str = Depends(correo_actual)):
    from guardadas import guardarVacante

    return con_mensaje(guardarVacante(correo, id_vacante))


@router.delete("/vacantes/{id_vacante}/guardada")
def quitar(id_vacante: int, correo: str = Depends(correo_actual)):
    from guardadas import quitarVacanteGuardada

    return con_mensaje(quitarVacanteGuardada(correo, id_vacante))


@router.post("/vacantes/{id_vacante}/compatibilidad")
def compatibilidad(id_vacante: int, correo: str = Depends(correo_actual)):
    """Lo calcula el agente; no se guarda (vive en el cliente)."""
    from compatibilidad import calcularCompatibilidad

    return con_datos(calcularCompatibilidad(correo, id_vacante))


@router.post("/vacantes/{id_vacante}/postular")
def postular(id_vacante: int, correo: str = Depends(correo_actual)):
    from postulaciones import registrarPostulacion

    return con_mensaje(registrarPostulacion(correo, id_vacante))


@router.get("/guardadas")
def listar_guardadas(correo: str = Depends(correo_actual)):
    from guardadas import consultarGuardadas

    return con_datos(consultarGuardadas(correo))


# ---------------------------------------------------------------------------
# Alerta y notificaciones (#17)
# ---------------------------------------------------------------------------
class Alerta(BaseModel):
    palabra_clave: str | None = None
    ubicacion: str | None = None
    salario_minimo: int | None = None
    modalidad: str | None = None


@router.get("/alerta")
def ver_alerta(correo: str = Depends(correo_actual)):
    from alertas import consultarAlerta

    return con_datos(consultarAlerta(correo))


@router.put("/alerta")
def guardar_alerta(cuerpo: Alerta, correo: str = Depends(correo_actual)):
    from alertas import guardarAlerta

    return con_mensaje(
        guardarAlerta(
            correo,
            (cuerpo.palabra_clave or "").strip() or None,
            cuerpo.ubicacion or None,
            cuerpo.salario_minimo or None,
            cuerpo.modalidad or None,
        )
    )


@router.delete("/alerta")
def desactivar_alerta(correo: str = Depends(correo_actual)):
    from alertas import eliminarAlerta

    return con_mensaje(eliminarAlerta(correo))


@router.get("/notificaciones")
def notificaciones(correo: str = Depends(correo_actual)):
    from alertas import consultarNotificaciones

    return con_datos(consultarNotificaciones(correo))


class Leidas(BaseModel):
    id_notificacion: int | None = None


@router.post("/notificaciones/leidas")
def marcar_leidas(cuerpo: Leidas, correo: str = Depends(correo_actual)):
    from alertas import marcarLeidas

    return con_mensaje(marcarLeidas(correo, cuerpo.id_notificacion))


# ---------------------------------------------------------------------------
# Recomendaciones (#11, #25, #27)
# ---------------------------------------------------------------------------
def _huella(preparado):
    """La `base` de prepararRecomendaciones, resumida: el cliente solo la compara.

    Así el perfil (aunque no tenga datos personales) no viaja al navegador.
    """
    return hashlib.sha256(preparado["base"].encode()).hexdigest()


def _estado(preparado):
    return {
        "base": _huella(preparado),
        "candidatas": [v["Id_vacante"] for v in preparado["candidatas"]],
        "faltantes": preparado["faltantes"],
    }


class Criterios(BaseModel):
    cargo_deseado: str | None = None
    modalidad: str | None = None
    ciudad: str | None = None


@router.get("/recomendaciones/criterios")
def ver_criterios(correo: str = Depends(correo_actual)):
    from recomendaciones import consultarCriterios

    return con_datos(consultarCriterios(correo))


@router.put("/recomendaciones/criterios")
def guardar_criterios(cuerpo: Criterios, correo: str = Depends(correo_actual)):
    from recomendaciones import guardarCriterios

    return con_mensaje(
        guardarCriterios(
            correo,
            (cuerpo.cargo_deseado or "").strip() or None,
            cuerpo.modalidad or None,
            cuerpo.ciudad or None,
        )
    )


@router.get("/recomendaciones/estado")
def estado_recomendaciones(correo: str = Depends(correo_actual)):
    """Sin llamar al agente: con esto el cliente decide si hay que pedir recomendaciones
    nuevas (la regla de RecomendacionesFront.actualizar_recomendaciones)."""
    from recomendaciones import prepararRecomendaciones

    exito, preparado = prepararRecomendaciones(correo)
    if not exito:
        return respuesta(False, preparado)
    return respuesta(True, None, _estado(preparado))


@router.post("/recomendaciones/generar")
def generar(correo: str = Depends(correo_actual)):
    """Llama al agente. Nada se guarda hasta que el usuario decide (decisión 7)."""
    from recomendaciones import generarRecomendaciones, prepararRecomendaciones

    exito, preparado = prepararRecomendaciones(correo)
    if not exito:
        return respuesta(False, preparado)
    exito, datos = generarRecomendaciones(correo, preparado)
    if not exito:
        return respuesta(False, datos)
    return respuesta(True, None, {**datos, **_estado(preparado)})


class Decision(BaseModel):
    decision: str  # "Interesa" | "Descartada"
    motivo: str | None = None


@router.post("/recomendaciones/{id_vacante}/decision")
def decidir(id_vacante: int, cuerpo: Decision, correo: str = Depends(correo_actual)):
    from recomendaciones import guardarDecision

    return con_mensaje(guardarDecision(correo, id_vacante, cuerpo.decision, cuerpo.motivo))


@router.get("/recomendaciones/interes")
def de_interes(correo: str = Depends(correo_actual)):
    from recomendaciones import consultarDeInteres

    return con_datos(consultarDeInteres(correo))
