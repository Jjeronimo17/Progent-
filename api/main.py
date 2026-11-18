"""API de Progent (FastAPI). Solo traduce HTTP <-> las funciones de Code/.

Levantar:  uvicorn main:app --reload --port 8000   (desde la carpeta api/)
Pruebas con el modelo simulado:  PROGENT_MODELO_SIMULADO=1 uvicorn main:app --port 8000
"""
import os

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import nucleo  # agrega Code/ al sys.path y carga el .env
from routers import cuenta, perfil, postulaciones, vacantes

app = FastAPI(title="Progent API", version="1.0")

# CORS solo para el frontend en desarrollo (Vite). En producción se sirve desde el mismo origen.
ORIGENES = [o for o in os.getenv("PROGENT_ORIGENES", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, nucleo.error_http)


@app.exception_handler(RequestValidationError)
def datos_invalidos(_request, exc: RequestValidationError):
    campos = ", ".join(str(e["loc"][-1]) for e in exc.errors())
    return JSONResponse(status_code=422, content=nucleo.respuesta(False, f"Revisa los datos enviados: {campos}."))


for modulo in (cuenta.auth, cuenta.resumen, perfil.router, vacantes.router, postulaciones.router):
    app.include_router(modulo)


@app.get("/api/salud")
def salud():
    return nucleo.respuesta(True, None, {"modelo_simulado": os.getenv("PROGENT_MODELO_SIMULADO") == "1"})


if os.getenv("PROGENT_MODELO_SIMULADO") == "1":
    # graph crea anthropic.Anthropic() al importarse: solo se importa en modo simulado
    # (en modo real, cada endpoint lo importa cuando lo necesita).
    import simulado

    simulado.activar()
