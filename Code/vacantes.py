import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()


def escaparComodines(texto):
    """Escapa los comodines de LIKE para buscar el texto tal como se escribió."""
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def consultarVacantes(palabra_clave=None, ubicacion=None, salario_minimo=None, modalidad=None):
    """Devuelve las vacantes abiertas, de la más reciente a la más antigua.

    Si llega una palabra clave, solo devuelve las vacantes cuyo cargo o
    descripción la contienen (sin distinguir mayúsculas ni tildes).
    Los filtros de ubicación, salario mínimo y modalidad se combinan entre sí
    y con la palabra clave. Con salario mínimo, las vacantes sin salario
    publicado quedan fuera.

    Retorna (True, lista) donde cada elemento es un diccionario con las
    columnas de la tabla Vacantes, o (False, mensaje) si falla la consulta.
    Una lista vacía significa que no hay vacantes que mostrar.
    """
    palabra_clave = (palabra_clave or "").strip()
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
                "Requisitos, Fecha_publicacion, Salario, Modalidad "
                "FROM Vacantes WHERE Estado = %s"
            )
            parametros = ("Abierta",)
            if palabra_clave:
                consultaVacantes += " AND (Cargo LIKE %s OR Descripcion LIKE %s)"
                patron = f"%{escaparComodines(palabra_clave)}%"
                parametros += (patron, patron)
            if ubicacion:
                consultaVacantes += " AND Ubicacion = %s"
                parametros += (ubicacion,)
            if salario_minimo:
                consultaVacantes += " AND Salario >= %s"
                parametros += (int(salario_minimo),)
            if modalidad:
                consultaVacantes += " AND Modalidad = %s"
                parametros += (modalidad,)
            consultaVacantes += " ORDER BY Fecha_publicacion DESC, Id_vacante DESC"
            cursor.execute(consultaVacantes, parametros)
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


def consultarVacante(id_vacante):
    """Devuelve una vacante por su id, esté abierta o cerrada.

    Retorna (True, diccionario) si existe, (True, None) si no existe
    o (False, mensaje) si falla la consulta.
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
            consultaVacante = (
                "SELECT Id_vacante, Cargo, Empresa, Ubicacion, Descripcion, "
                "Requisitos, Estado, Fecha_publicacion, Salario, Modalidad "
                "FROM Vacantes WHERE Id_vacante = %s"
            )
            parametro = (id_vacante,)
            cursor.execute(consultaVacante, parametro)
            resultado = cursor.fetchone()
            return True, resultado
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo cargar la vacante, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarUbicaciones():
    """Retorna (True, lista de ubicaciones con vacantes abiertas) o (False, mensaje)."""
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        if conexion.is_connected():
            cursor = conexion.cursor()
            consulta = (
                "SELECT DISTINCT Ubicacion FROM Vacantes WHERE Estado = %s ORDER BY Ubicacion"
            )
            cursor.execute(consulta, ("Abierta",))
            return True, [fila[0] for fila in cursor.fetchall()]
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron cargar las ubicaciones, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
