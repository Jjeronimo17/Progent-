"""Piezas compartidas por todos los routers: respuesta uniforme, sesión y archivos.

La API no reescribe la lógica: solo traduce HTTP <-> las funciones de Code/.
"""
import base64
import datetime as dt
import decimal
import os
import secrets
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

import jwt
from fastapi import Cookie, HTTPException, Response
from fastapi.responses import JSONResponse

RAIZ = Path(__file__).resolve().parent.parent
CODE = RAIZ / "Code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

# La lógica lee el .env de la raíz del repositorio (load_dotenv en cada módulo).
from dotenv import load_dotenv  # noqa: E402

load_dotenv(RAIZ / ".env")

COOKIE_SESION = "progent_sesion"
HORAS_SESION = 8
_SECRETO = os.getenv("PROGENT_JWT_SECRETO") or secrets.token_hex(32)
_COOKIE_SEGURA = os.getenv("PROGENT_COOKIE_SEGURA", "0") == "1"


# ---------------------------------------------------------------------------
# Respuesta uniforme: { "ok": bool, "mensaje": str | null, "datos": ... }
# ---------------------------------------------------------------------------
def serializar(valor):
    """Convierte lo que devuelve MySQL a JSON: fechas ISO 8601, Decimal a número.

    Los bytes de archivos nunca viajan en el JSON (se descargan aparte).
    """
    if isinstance(valor, dict):
        return {str(k): serializar(v) for k, v in valor.items() if not isinstance(v, (bytes, bytearray))}
    if isinstance(valor, (list, tuple, set)):
        return [serializar(v) for v in valor]
    if isinstance(valor, (dt.datetime, dt.date, dt.time)):
        return valor.isoformat()
    if isinstance(valor, dt.timedelta):
        return valor.total_seconds()
    if isinstance(valor, decimal.Decimal):
        return float(valor)
    if isinstance(valor, (bytes, bytearray)):
        return None
    return valor


def respuesta(ok=True, mensaje=None, datos=None):
    return {"ok": bool(ok), "mensaje": mensaje, "datos": serializar(datos)}


def con_datos(resultado):
    """(exito, datos_o_mensaje) -> respuesta. Si falla, el segundo valor es el mensaje."""
    exito, valor = resultado
    if exito:
        return respuesta(True, None, valor)
    return respuesta(False, valor if isinstance(valor, str) else None, None if isinstance(valor, str) else valor)


def con_mensaje(resultado):
    """(exito, mensaje) -> respuesta con el mensaje listo para mostrar."""
    exito, mensaje = resultado
    return respuesta(exito, mensaje)


# ---------------------------------------------------------------------------
# Sesión: JWT en una cookie httpOnly. El correo sale SIEMPRE del token.
# ---------------------------------------------------------------------------
def abrir_sesion(response: Response, correo: str):
    ahora = dt.datetime.now(dt.timezone.utc)
    token = jwt.encode(
        {"sub": correo, "iat": ahora, "exp": ahora + dt.timedelta(hours=HORAS_SESION)},
        _SECRETO,
        algorithm="HS256",
    )
    response.set_cookie(
        COOKIE_SESION,
        token,
        httponly=True,
        samesite="lax",
        secure=_COOKIE_SEGURA,
        max_age=HORAS_SESION * 3600,
        path="/",
    )


def cerrar_sesion(response: Response):
    response.delete_cookie(COOKIE_SESION, path="/")


def correo_actual(progent_sesion: str | None = Cookie(default=None)) -> str:
    """Dependencia: el correo del usuario de la sesión, o 401."""
    if not progent_sesion:
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar.")
    try:
        datos = jwt.decode(progent_sesion, _SECRETO, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Tu sesión expiró. Inicia sesión de nuevo.")
    return datos["sub"]


def error_http(_request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=respuesta(False, str(exc.detail)))


# ---------------------------------------------------------------------------
# Archivos
# ---------------------------------------------------------------------------
def descarga(datos: bytes, nombre: str, tipo: str | None) -> Response:
    """Descarga con el nombre original, también con tildes (RFC 5987).

    `filename` lleva una versión ASCII para navegadores viejos; `filename*` el nombre real.
    Sin `filename*`, el navegador corta el nombre en la primera tilde y el archivo
    queda sin extensión.
    """
    ascii_nombre = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode() or "archivo"
    ascii_nombre = ascii_nombre.replace('"', "")
    disposicion = f"attachment; filename=\"{ascii_nombre}\"; filename*=UTF-8''{quote(nombre)}"
    return Response(
        content=bytes(datos),
        media_type=tipo or "application/octet-stream",
        headers={"Content-Disposition": disposicion},
    )


def base64_de(datos: bytes) -> str:
    return base64.b64encode(datos).decode()
