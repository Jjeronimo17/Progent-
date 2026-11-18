import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()

FALTA_DATOS_BASICOS = "Tus datos básicos (nombre, correo de contacto, ubicación y ocupación)."
FALTA_EXPERIENCIA_O_EDUCACION = "Al menos una experiencia laboral o una educación."


def conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def calcularFaltantes(cursor, correo):
    """Lista lo que le falta al perfil para poder postularse.

    Un perfil está completo si tiene datos básicos y al menos una
    experiencia laboral o una educación.
    """
    faltantes = []

    cursor.execute("SELECT COUNT(*) FROM informacion_usuarios WHERE Correos = %s", (correo,))
    if cursor.fetchone()[0] == 0:
        faltantes.append(FALTA_DATOS_BASICOS)

    cursor.execute(
        "SELECT (SELECT COUNT(*) FROM Experiencia WHERE Correos_experiencia = %s) + "
        "(SELECT COUNT(*) FROM Educacion WHERE Correos_educacion = %s)",
        (correo, correo),
    )
    if cursor.fetchone()[0] == 0:
        faltantes.append(FALTA_EXPERIENCIA_O_EDUCACION)

    return faltantes


def mensajeFaltantes(faltantes):
    lineas = "\n".join(f"- {f}" for f in faltantes)
    return (
        "Para postularte necesitas completar tu perfil. Te falta:\n"
        f"{lineas}\n\nComplétalo en **Mi perfil → Llenar mi perfil manualmente**."
    )


def faltantesPerfil(correo):
    """Retorna (True, lista de faltantes) o (False, mensaje). Lista vacía = perfil completo."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            return True, calcularFaltantes(cursor, correo)
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo revisar tu perfil, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def registrarPostulacion(correo, id_vacante):
    """Registra la postulación del usuario a una vacante abierta.

    Antes de insertar revisa que la vacante siga abierta y que el perfil
    esté completo. Retorna (True, mensaje) o (False, mensaje).
    """
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()

            cursor.execute("SELECT Estado FROM Vacantes WHERE Id_vacante = %s", (id_vacante,))
            vacante = cursor.fetchone()
            if vacante is None:
                return False, "Esta vacante ya no existe."
            if vacante[0] != "Abierta":
                return False, "Esta vacante fue cerrada y ya no recibe postulaciones."

            faltantes = calcularFaltantes(cursor, correo)
            if faltantes:
                return False, mensajeFaltantes(faltantes)

            cursor.execute(
                "SELECT COUNT(*) FROM archivos_usuarios WHERE Correos_usuarios = %s", (correo,)
            )
            if cursor.fetchone()[0] == 0:
                return False, "Para postularte necesitas cargar tu hoja de vida."

            insertar = (
                "INSERT INTO Postulaciones(Correos_postulacion, Id_vacante_postulacion) "
                "VALUES (%s, %s)"
            )
            cursor.execute(insertar, (correo, id_vacante))
            # Copia de la hoja de vida usada: así se sabe cuál quedó asociada aunque
            # después el usuario la cambie en su perfil (historia #20).
            cursor.execute(
                "INSERT INTO Cv_postulacion(Id_postulacion_cv, Nombre_archivo, Tipo, Archivo_bytes) "
                "SELECT %s, nombre_archivo, tipo, archivo_bytes FROM archivos_usuarios "
                "WHERE Correos_usuarios = %s",
                (cursor.lastrowid, correo),
            )
            conexion.commit()
            return True, "Tu postulación quedó registrada en tu panel de seguimiento."
        return False, (
            "No se pudo conectar a la base de datos y tu postulación **no** quedó "
            "registrada. Intenta de nuevo."
        )
    except Error as e:
        if e.errno == 1062:
            return False, "Ya te postulaste a esta vacante."
        print(f"Fallo en las operaciones de arriba {e}")
        return False, (
            "Ocurrió un error y tu postulación **no** quedó registrada. Intenta de nuevo."
        )
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarPostulacion(correo, id_vacante):
    """Retorna (True, diccionario o None) según si el usuario ya se postuló, o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = (
                "SELECT p.Id_postulacion, p.Fecha_postulacion, p.Estado, c.Nombre_archivo AS Cv "
                "FROM Postulaciones p LEFT JOIN Cv_postulacion c ON c.Id_postulacion_cv = p.Id_postulacion "
                "WHERE p.Correos_postulacion = %s AND p.Id_vacante_postulacion = %s"
            )
            cursor.execute(consulta, (correo, id_vacante))
            return True, cursor.fetchone()
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo revisar tu postulación, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarPostulaciones(correo):
    """Retorna (True, lista) con las postulaciones del usuario, la más reciente primero, o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = (
                "SELECT p.Id_postulacion, p.Fecha_postulacion, p.Estado, "
                "v.Id_vacante, v.Cargo, v.Empresa, v.Ubicacion, v.Descripcion, "
                "v.Requisitos, v.Fecha_publicacion, v.Estado AS Estado_vacante, "
                "c.Nombre_archivo AS Cv "
                "FROM Postulaciones p "
                "JOIN Vacantes v ON v.Id_vacante = p.Id_vacante_postulacion "
                "LEFT JOIN Cv_postulacion c ON c.Id_postulacion_cv = p.Id_postulacion "
                "WHERE p.Correos_postulacion = %s "
                "ORDER BY p.Fecha_postulacion DESC, p.Id_postulacion DESC"
            )
            cursor.execute(consulta, (correo,))
            return True, cursor.fetchall()
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron cargar tus postulaciones, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
