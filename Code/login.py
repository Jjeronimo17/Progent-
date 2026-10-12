import hashlib
import os
import re
import secrets

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()

CANTIDAD_ITERACIONES = 600000


def generarSalt():
    salt = secrets.token_hex(16)
    return salt


def hashing(passwordUser):
    salt = generarSalt()
    saltBytes = salt.encode()
    passwordUserBytes = passwordUser.encode()
    passwordHashedBytes = hashlib.pbkdf2_hmac(
        "sha256", passwordUserBytes, saltBytes, CANTIDAD_ITERACIONES
    )
    passwordHashed = passwordHashedBytes.hex()
    return passwordHashed, salt


def guardarDataBase(correo, passwordUser):
    correo = correo.lower()
    passwordHash, salt = hashing(passwordUser)
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
            atributos = (correo, "")
            resultado = cursor.callproc("verificar_usuario", atributos)
            verificacion = resultado[1]
            miRegex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            resultado = re.search(miRegex, correo)
            if verificacion == "Usuario No Disponible":
                return False, "Correo asociado a una cuenta, use otro"
            elif not (resultado):
                return False, "Ingrese una direccion de correo valida"
            else:
                sql_insertar = (
                    "INSERT INTO usuarios(Correos, Salt, Hashed) VALUES (%s, %s, %s)"
                )
                datos = (correo, salt, passwordHash)
                cursor.execute(sql_insertar, datos)
                conexion.commit()
                return True, "Registro exitoso"

    except Error as e:
        print(f"Error durante las operaciones {e}")
        return False, "No se pudo completar el registro. Intenta de nuevo."

    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def iniciarSesion(correo, passwordUser):
    passwordCorrecto = False
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
            correo_buscar = correo
            sql_selectSalt = "SELECT SALT FROM Usuarios WHERE Correos = %s"
            cursor.execute(sql_selectSalt, (correo_buscar,))
            saltTuple = cursor.fetchone()
            salt = saltTuple[0]
            sql_selectHash = "SELECT Hashed FROM Usuarios WHERE Correos = %s"
            cursor.execute(sql_selectHash, (correo_buscar,))
            hashedTuple = cursor.fetchone()
            hashed = hashedTuple[0]
            saltBytes = salt.encode()
            passwordUserBytes = passwordUser.encode()
            passwordVerificarBytes = hashlib.pbkdf2_hmac(
                "sha256", passwordUserBytes, saltBytes, CANTIDAD_ITERACIONES
            )
            passwordVerificar = passwordVerificarBytes.hex()
            verificacion = secrets.compare_digest(passwordVerificar, hashed)
            if verificacion:
                passwordCorrecto = True
                return passwordCorrecto
    except Error as e:
        print(f"Error durante las operaciones {e}")
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
