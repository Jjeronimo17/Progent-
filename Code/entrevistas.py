import os
from datetime import datetime

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()

# Se recuerda la entrevista desde esta cantidad de días antes.
DIAS_RECORDATORIO = 7
# En estas etapas el proceso terminó: ya no hay entrevista que recordar.
ESTADOS_SIN_RECORDATORIO = ("Rechazado", "Retirado")


def conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def textoFecha(fecha):
    return f"{fecha:%d/%m/%Y} a las {fecha:%H:%M}"


def cuandoEs(fecha, ahora=None):
    """"hoy", "mañana" o "en N días", según el día de la entrevista."""
    dias = (fecha.date() - (ahora or datetime.now()).date()).days
    if dias <= 0:
        return "hoy"
    if dias == 1:
        return "mañana"
    return f"en {dias} días"


def guardarEntrevista(correo, id_postulacion, fecha):
    """El usuario informa la fecha de su próxima entrevista (decisión 5: él la reporta).

    Si ya había una, la reemplaza. Retorna (True, mensaje) o (False, mensaje).
    """
    if fecha is None:
        return False, "Elige la fecha y la hora de la entrevista."
    if fecha <= datetime.now():
        return False, "Esa fecha ya pasó: informa la fecha de tu próxima entrevista."
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM Postulaciones WHERE Id_postulacion = %s AND Correos_postulacion = %s",
                (id_postulacion, correo),
            )
            if cursor.fetchone()[0] == 0:
                return False, "Esta postulación no existe."
            cursor.execute(
                "INSERT INTO Entrevistas(Id_postulacion_entrevista, Fecha_entrevista) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE Fecha_entrevista = VALUES(Fecha_entrevista), Fecha_registro = NOW()",
                (id_postulacion, fecha),
            )
            conexion.commit()
            return True, f"Guardaste tu entrevista del {textoFecha(fecha)}. Te la recordaré cuando se acerque."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo guardar la entrevista, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def quitarEntrevista(correo, id_postulacion):
    """Borra la entrevista informada (por ejemplo, si se canceló)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute(
                "DELETE e FROM Entrevistas e JOIN Postulaciones p ON p.Id_postulacion = e.Id_postulacion_entrevista "
                "WHERE e.Id_postulacion_entrevista = %s AND p.Correos_postulacion = %s",
                (id_postulacion, correo),
            )
            conexion.commit()
            return True, "Quitaste la entrevista de esta postulación."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo quitar la entrevista, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarRecordatorios(correo):
    """Entrevistas pendientes que se acercan (de ahora a DIAS_RECORDATORIO días), la más próxima primero.

    Las que ya pasaron dejan de ser pendientes, y las de procesos rechazados o
    retirados no se recuerdan. Retorna (True, lista) o (False, mensaje).
    """
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = (
                "SELECT p.Id_postulacion, e.Fecha_entrevista, v.Cargo, v.Empresa FROM Entrevistas e "
                "JOIN Postulaciones p ON p.Id_postulacion = e.Id_postulacion_entrevista "
                "JOIN Vacantes v ON v.Id_vacante = p.Id_vacante_postulacion "
                "WHERE p.Correos_postulacion = %s AND p.Estado NOT IN (%s, %s) "
                "AND e.Fecha_entrevista >= NOW() "
                "AND e.Fecha_entrevista <= NOW() + INTERVAL %s DAY "
                "ORDER BY e.Fecha_entrevista"
            )
            cursor.execute(consulta, (correo, *ESTADOS_SIN_RECORDATORIO, DIAS_RECORDATORIO))
            return True, cursor.fetchall()
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron revisar tus entrevistas, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
