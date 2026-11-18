"""Nombres de columnas de las tablas que datosUsuario devuelve como tuplas (SELECT *).

Se leen de la base al primer uso, así la API sigue funcionando si el esquema cambia.
"""
import os
from functools import lru_cache

import mysql.connector


@lru_cache(maxsize=None)
def de(tabla: str) -> tuple[str, ...]:
    conexion = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    try:
        cursor = conexion.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {tabla}")
        return tuple(fila[0] for fila in cursor.fetchall())
    finally:
        conexion.close()


def fila(tabla, valores):
    return None if valores is None else dict(zip(de(tabla), valores))


def filas(tabla, lista):
    return [fila(tabla, v) for v in (lista or [])]
