import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()


def conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def guardarVacante(correo, id_vacante):
    """Agrega una vacante a la lista de guardadas. Retorna (True, mensaje) o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            insertar = (
                "INSERT INTO Vacantes_guardadas(Correos_guardada, Id_vacante_guardada) "
                "VALUES (%s, %s)"
            )
            cursor.execute(insertar, (correo, id_vacante))
            conexion.commit()
            return True, "Guardaste esta vacante. La encuentras en **Guardadas**."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        if e.errno == 1062:
            return True, "Esta vacante ya estaba en tus guardadas."
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo guardar la vacante, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def quitarVacanteGuardada(correo, id_vacante):
    """Quita solo esa vacante de la lista del usuario. Retorna (True, mensaje) o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            borrar = (
                "DELETE FROM Vacantes_guardadas "
                "WHERE Correos_guardada = %s AND Id_vacante_guardada = %s"
            )
            cursor.execute(borrar, (correo, id_vacante))
            conexion.commit()
            return True, "Quitaste la vacante de tus guardadas."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo quitar la vacante, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def estaGuardada(correo, id_vacante):
    """Retorna (True, True/False) según si el usuario guardó la vacante, o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            consulta = (
                "SELECT COUNT(*) FROM Vacantes_guardadas "
                "WHERE Correos_guardada = %s AND Id_vacante_guardada = %s"
            )
            cursor.execute(consulta, (correo, id_vacante))
            return True, cursor.fetchone()[0] > 0
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo revisar si guardaste esta vacante, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarGuardadas(correo):
    """Retorna (True, lista) con las vacantes guardadas, la más reciente primero, o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = (
                "SELECT v.Id_vacante, v.Cargo, v.Empresa, v.Ubicacion, v.Estado, "
                "g.Fecha_guardada FROM Vacantes_guardadas g "
                "JOIN Vacantes v ON v.Id_vacante = g.Id_vacante_guardada "
                "WHERE g.Correos_guardada = %s "
                "ORDER BY g.Fecha_guardada DESC, g.Id_guardada DESC"
            )
            cursor.execute(consulta, (correo,))
            return True, cursor.fetchall()
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron cargar tus vacantes guardadas, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
