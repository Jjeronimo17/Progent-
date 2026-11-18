"""auth (crear cuenta, iniciar y cerrar sesión) y resumen (contador y recordatorios)."""
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from nucleo import abrir_sesion, cerrar_sesion, correo_actual, respuesta

auth = APIRouter(prefix="/api/auth", tags=["auth"])
resumen = APIRouter(prefix="/api", tags=["resumen"])


class Credenciales(BaseModel):
    correo: str = ""
    contrasena: str = ""


@auth.post("/registro")
def registro(cuerpo: Credenciales):
    from login import guardarDataBase

    correo, clave = cuerpo.correo.strip(), cuerpo.contrasena
    # Las mismas validaciones (y textos) que LoginFront.formulario_crear_cuenta.
    if not correo or not clave:
        return respuesta(False, "Completa el correo y la contraseña.")
    if "@" not in correo:
        return respuesta(False, "Escribe un correo válido.")
    if len(clave) < 8:
        return respuesta(False, "La contraseña debe tener al menos 8 caracteres.")
    exito, mensaje = guardarDataBase(correo, clave)
    return respuesta(exito, mensaje)


@auth.post("/login")
def login(cuerpo: Credenciales, response: Response):
    from login import iniciarSesion

    correo, clave = cuerpo.correo.strip(), cuerpo.contrasena
    if not correo or not clave:
        return respuesta(False, "Escribe tu correo y tu contraseña.")
    # El registro guarda el correo en minúsculas; el login lo busca igual.
    correo = correo.lower()
    try:
        correcto = iniciarSesion(correo, clave)
    except TypeError:
        # Correo sin cuenta: iniciarSesion no lo contempla (ver CAMBIOS_LOGICA.md).
        correcto = False
    if not correcto:
        return respuesta(False, "Correo o contraseña incorrectos.")
    abrir_sesion(response, correo)
    return respuesta(True, None, {"correo": correo})


@auth.post("/logout")
def logout(response: Response):
    cerrar_sesion(response)
    return respuesta(True)


@auth.get("/sesion")
def sesion(correo: str = Depends(correo_actual)):
    return respuesta(True, None, {"correo": correo})


@resumen.get("/resumen")
def ver_resumen(correo: str = Depends(correo_actual)):
    """Lo que el menú muestra en cada visita: no leídas (#17) y recordatorios (#28).

    revisarAlertas corre aquí porque no hay tareas en segundo plano. Si algo falla,
    el menú se muestra sin el contador o sin recordatorios, como en Streamlit.
    """
    from alertas import revisarAlertas
    from entrevistas import consultarRecordatorios

    exito, sin_leer = revisarAlertas(correo)
    exito_r, recordatorios = consultarRecordatorios(correo)
    return respuesta(
        True,
        None,
        {
            "sin_leer": sin_leer if exito else 0,
            "recordatorios": recordatorios if exito_r else [],
        },
    )
