import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

from vacantes import escaparComodines

load_dotenv()


def conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def guardarAlerta(correo, palabra_clave, ubicacion, salario_minimo, modalidad):
    """Crea o reemplaza la alerta del usuario con los filtros dados.

    Exige al menos un criterio, para no avisar de todas las vacantes.
    Solo cuentan como nuevas las vacantes publicadas después de guardar la alerta.
    Retorna (True, mensaje) o (False, mensaje).
    """
    palabra_clave = (palabra_clave or "").strip() or None
    if not (palabra_clave or ubicacion or salario_minimo or modalidad):
        return False, "Elige al menos un filtro o una palabra clave para crear la alerta."
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("SELECT COALESCE(MAX(Id_vacante), 0) FROM Vacantes")
            ultima = cursor.fetchone()[0]
            guardar = (
                "INSERT INTO Alertas(Correos_alerta, Palabra_clave, Ubicacion, Salario_minimo, "
                "Modalidad, Ultima_vacante_revisada, Fecha_creacion) "
                "VALUES (%s, %s, %s, %s, %s, %s, NOW()) "
                "ON DUPLICATE KEY UPDATE Palabra_clave = VALUES(Palabra_clave), "
                "Ubicacion = VALUES(Ubicacion), Salario_minimo = VALUES(Salario_minimo), "
                "Modalidad = VALUES(Modalidad), "
                "Ultima_vacante_revisada = VALUES(Ultima_vacante_revisada), Fecha_creacion = NOW()"
            )
            salario = int(salario_minimo) if salario_minimo else None
            cursor.execute(guardar, (correo, palabra_clave, ubicacion, salario, modalidad, ultima))
            conexion.commit()
            return True, "Alerta guardada. Te avisaremos cuando se publique una vacante que la cumpla."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo guardar la alerta, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarAlerta(correo):
    """Retorna (True, diccionario o None) con la alerta del usuario, o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = (
                "SELECT Palabra_clave, Ubicacion, Salario_minimo, Modalidad, Fecha_creacion "
                "FROM Alertas WHERE Correos_alerta = %s"
            )
            cursor.execute(consulta, (correo,))
            return True, cursor.fetchone()
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo cargar tu alerta, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def eliminarAlerta(correo):
    """Desactiva (borra) la alerta. Las notificaciones ya recibidas se conservan."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM Alertas WHERE Correos_alerta = %s", (correo,))
            conexion.commit()
            return True, "Desactivaste tu alerta."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo desactivar la alerta, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def revisarAlertas(correo):
    """Crea las notificaciones de vacantes nuevas que cumplen la alerta del usuario.

    Se llama cada vez que el usuario usa Progent (no hay procesos en segundo plano).
    Solo revisa vacantes publicadas después de la última revisión y solo crea
    notificaciones si hay coincidencias: sin vacantes nuevas, no genera nada.
    Retorna (True, cantidad de notificaciones sin leer) o (False, mensaje).
    """
    try:
        conexion = conectar()
        if not conexion.is_connected():
            return False, "No se pudo conectar a la base de datos, intente de nuevo"
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT Palabra_clave, Ubicacion, Salario_minimo, Modalidad, "
            "Ultima_vacante_revisada FROM Alertas WHERE Correos_alerta = %s",
            (correo,),
        )
        alerta = cursor.fetchone()

        if alerta:
            palabra_clave, ubicacion, salario_minimo, modalidad, ultima = alerta
            cursor.execute("SELECT COALESCE(MAX(Id_vacante), 0) FROM Vacantes")
            hasta = cursor.fetchone()[0]

            if hasta > ultima:
                consulta = (
                    "SELECT Id_vacante FROM Vacantes WHERE Estado = 'Abierta' "
                    "AND Id_vacante > %s AND Id_vacante <= %s"
                )
                parametros = (ultima, hasta)
                if palabra_clave:
                    consulta += " AND (Cargo LIKE %s OR Descripcion LIKE %s)"
                    patron = f"%{escaparComodines(palabra_clave)}%"
                    parametros += (patron, patron)
                if ubicacion:
                    consulta += " AND Ubicacion = %s"
                    parametros += (ubicacion,)
                if salario_minimo:
                    consulta += " AND Salario >= %s"
                    parametros += (salario_minimo,)
                if modalidad:
                    consulta += " AND Modalidad = %s"
                    parametros += (modalidad,)
                cursor.execute(consulta, parametros)
                nuevas = [fila[0] for fila in cursor.fetchall()]

                if nuevas:
                    cursor.executemany(
                        "INSERT IGNORE INTO Notificaciones(Correos_notificacion, "
                        "Id_vacante_notificacion) VALUES (%s, %s)",
                        [(correo, id_vacante) for id_vacante in nuevas],
                    )
                cursor.execute(
                    "UPDATE Alertas SET Ultima_vacante_revisada = %s WHERE Correos_alerta = %s",
                    (hasta, correo),
                )
                conexion.commit()

        cursor.execute(
            "SELECT COUNT(*) FROM Notificaciones WHERE Correos_notificacion = %s AND Leida = 0",
            (correo,),
        )
        return True, cursor.fetchone()[0]
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron revisar tus alertas, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarNotificaciones(correo):
    """Retorna (True, lista) con las notificaciones, la más reciente primero, o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = (
                "SELECT n.Id_notificacion, n.Fecha_notificacion, n.Leida, v.Id_vacante, "
                "v.Cargo, v.Empresa, v.Ubicacion, v.Estado, v.Fecha_publicacion "
                "FROM Notificaciones n "
                "JOIN Vacantes v ON v.Id_vacante = n.Id_vacante_notificacion "
                "WHERE n.Correos_notificacion = %s "
                "ORDER BY n.Leida ASC, n.Fecha_notificacion DESC, n.Id_notificacion DESC"
            )
            cursor.execute(consulta, (correo,))
            return True, cursor.fetchall()
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron cargar tus notificaciones, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def marcarLeidas(correo, id_notificacion=None):
    """Marca como leída una notificación, o todas si no se indica cuál."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            consulta = "UPDATE Notificaciones SET Leida = 1 WHERE Correos_notificacion = %s"
            parametros = (correo,)
            if id_notificacion is not None:
                consulta += " AND Id_notificacion = %s"
                parametros += (id_notificacion,)
            cursor.execute(consulta, parametros)
            conexion.commit()
            return True, "Notificaciones marcadas como leídas."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron actualizar tus notificaciones, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
