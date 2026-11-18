"""Pruebas de la API contra una base MySQL/MariaDB de prueba y el modelo SIMULADO.

Requiere la base cargada con:
    mysql --default-character-set=utf8mb4 < db/schema.sql
y el .env de PRUEBA en la raíz del repositorio. Correr desde api/:  pytest -q
"""
import os
import pathlib
import sys
import uuid

import pytest

os.environ["PROGENT_MODELO_SIMULADO"] = "1"
API = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API))

import mysql.connector  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

ARCHIVOS = pathlib.Path(os.getenv("PROGENT_ARCHIVOS_PRUEBA", API / "tests" / "archivos"))
MODO = pathlib.Path("/tmp/modo_modelo.txt")


def sql(consulta, parametros=()):
    conexion = mysql.connector.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"), database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
    )
    try:
        cursor = conexion.cursor()
        cursor.execute(consulta, parametros)
        filas = cursor.fetchall() if cursor.with_rows else None
        conexion.commit()
        return filas
    finally:
        conexion.close()


def modo(valor):
    MODO.write_text(valor)


@pytest.fixture(autouse=True)
def modelo_normal():
    modo("normal")
    yield
    modo("normal")


def nuevo_usuario(cliente=None, entrar=True):
    """Crea una cuenta con un correo único y (si se pide) abre su sesión."""
    cliente = cliente or TestClient(main.app)
    correo = f"prueba_{uuid.uuid4().hex[:10]}@ejemplo.com"
    r = cliente.post("/api/auth/registro", json={"correo": correo, "contrasena": "clave1234"})
    assert r.json()["ok"], r.json()
    if entrar:
        r = cliente.post("/api/auth/login", json={"correo": correo, "contrasena": "clave1234"})
        assert r.json()["ok"], r.json()
    return cliente, correo


def perfil_completo(correo):
    sql(
        "INSERT INTO informacion_usuarios VALUES (%s,'Persona Prueba',30,'3000000000',%s,'Medellín','Analista')",
        (correo, correo),
    )
    sql(
        "INSERT INTO Educacion(Correos_educacion,Institucion_educativa,Titulo_Carrera_Grado,Fecha_inicio,Estado_estudio)"
        " VALUES (%s,'Universidad Inventada','Ingeniería','2020-01-01','Graduado')",
        (correo,),
    )


def cv_guardado(correo, nombre="cv.pdf"):
    sql(
        "INSERT INTO archivos_usuarios VALUES (%s,%s,'application/pdf',%s)",
        (correo, nombre, b"%PDF-1.4\n"),
    )


def id_vacante_abierta():
    return sql("SELECT Id_vacante FROM Vacantes WHERE Estado='Abierta' ORDER BY Id_vacante LIMIT 1")[0][0]


def archivo(nombre):
    return (ARCHIVOS / nombre).read_bytes()
