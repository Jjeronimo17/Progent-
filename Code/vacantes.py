import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()


def consultarVacantes():
    """Devuelve las vacantes abiertas, de la más reciente a la más antigua.

    Retorna (True, lista) donde cada elemento es un diccionario con las
    columnas de la tabla Vacantes, o (False, mensaje) si falla la consulta.
    Una lista vacía significa que no hay vacantes disponibles.
    """
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consultaVacantes = (
                "SELECT Id_vacante, Cargo, Empresa, Ubicacion, Descripcion, "
                "Requisitos, Fecha_publicacion FROM Vacantes "
                "WHERE Estado = %s ORDER BY Fecha_publicacion DESC, Id_vacante DESC"
            )
            parametro = ("Abierta",)
            cursor.execute(consultaVacantes, parametro)
            resultado = cursor.fetchall()
            return True, resultado
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron cargar las vacantes, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
