import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()

TIPOS_DOCUMENTO = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
# Los primeros bytes de cada formato: así se detecta un archivo renombrado.
FIRMAS = {"pdf": b"%PDF", "docx": b"PK\x03\x04"}
MAX_BYTES = 2 * 1024 * 1024


def conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def validarDocumento(nombre_archivo, datos, max_bytes=MAX_BYTES):
    """Valida que sea un PDF o Word (.docx) real y no muy pesado.

    Retorna (True, tipo MIME) o (False, mensaje de error).
    """
    extension = nombre_archivo.rsplit(".", 1)[-1].lower() if "." in nombre_archivo else ""
    if extension not in TIPOS_DOCUMENTO:
        return False, "Formato no válido: sube un archivo PDF o Word (.docx)."
    if not datos:
        return False, "El archivo está vacío."
    if len(datos) > max_bytes:
        megas = len(datos) / (1024 * 1024)
        return False, f"El archivo pesa {megas:.1f} MB y el máximo es {max_bytes // (1024 * 1024)} MB."
    if not datos.startswith(FIRMAS[extension]):
        return False, f"El archivo no es un {extension.upper()} válido: su contenido no corresponde a la extensión."
    return True, TIPOS_DOCUMENTO[extension]


def guardarCarta(correo, id_postulacion, nombre_archivo, datos):
    """Adjunta la carta a una postulación del usuario. Si ya había una, la reemplaza.

    Retorna (True, mensaje) o (False, mensaje). Si el archivo no es válido, no guarda nada.
    """
    valido, tipo = validarDocumento(nombre_archivo, datos)
    if not valido:
        return False, tipo
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM Postulaciones WHERE Id_postulacion = %s "
                "AND Correos_postulacion = %s",
                (id_postulacion, correo),
            )
            if cursor.fetchone()[0] == 0:
                return False, "Esta postulación no existe."
            guardar = (
                "INSERT INTO Cartas_presentacion(Id_postulacion_carta, Nombre_archivo, Tipo, "
                "Archivo_bytes) VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE Nombre_archivo = VALUES(Nombre_archivo), "
                "Tipo = VALUES(Tipo), Archivo_bytes = VALUES(Archivo_bytes), Fecha_carga = NOW()"
            )
            cursor.execute(guardar, (id_postulacion, nombre_archivo, tipo, datos))
            conexion.commit()
            return True, f"Carta «{nombre_archivo}» adjunta a tu postulación."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo guardar la carta, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarCarta(correo, id_postulacion):
    """Retorna (True, diccionario o None) con la carta de la postulación, o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = (
                "SELECT c.Nombre_archivo, c.Tipo, c.Archivo_bytes, c.Fecha_carga "
                "FROM Cartas_presentacion c JOIN Postulaciones p "
                "ON p.Id_postulacion = c.Id_postulacion_carta "
                "WHERE c.Id_postulacion_carta = %s AND p.Correos_postulacion = %s"
            )
            cursor.execute(consulta, (id_postulacion, correo))
            return True, cursor.fetchone()
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo cargar la carta, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def guardarCvPerfil(correo, nombre_archivo, datos):
    """Guarda la hoja de vida en el perfil (tabla archivos_usuarios) si aún no tiene una.

    Valida el formato y el contenido como las cartas, pero permite hasta 5 MB.
    Retorna (True, mensaje) o (False, mensaje).
    """
    valido, tipo = validarDocumento(nombre_archivo, datos, max_bytes=5 * 1024 * 1024)
    if not valido:
        return False, tipo
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute(
                "INSERT INTO archivos_usuarios(Correos_usuarios, nombre_archivo, tipo, archivo_bytes) "
                "VALUES (%s, %s, %s, %s)",
                (correo, nombre_archivo, tipo, datos),
            )
            conexion.commit()
            return True, f"Hoja de vida «{nombre_archivo}» guardada en tu perfil."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        if e.errno == 1062:
            return False, "Ya tienes una hoja de vida guardada en tu perfil."
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo guardar la hoja de vida, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
