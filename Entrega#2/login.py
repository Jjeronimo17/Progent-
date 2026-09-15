import mysql.connector
from mysql.connector import Error
import secrets
import hashlib
import re

CANTIDAD_ITERACIONES = 600000


correo = ""
passwordUser = ""


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
    correo = input("Ingrese un nombre de usuario: ")
    passwordUser = input("Ingrese una contraseña: ")
    passwordHash, salt = hashing(passwordUser)
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            port=3306,
            database="progent_usuarios",
            user="root",
            password="20081996Jeronimo13",
        )
        if conexion.is_connected():
            cursor = conexion.cursor()
            atributos = (correo, "")
            resultado = cursor.callproc("verificar_usuario", atributos)
            verificacion = resultado[1]
            miRegex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            resultado = re.search(miRegex, correo)
            if verificacion == "Usuario No Disponible":
                print("Correo asociado a una cuenta, use otro")
            elif not (resultado):
                print("Ingrese una direccion de correo valida")
            else:
                sql_insertar = (
                    "INSERT INTO usuarios(Correos, Salt, Hashed) VALUES (%s, %s, %s)"
                )
                datos = (correo, salt, passwordHash)
                cursor.execute(sql_insertar, datos)
                conexion.commit()
                print("Usuario Creado con exito")

    except Error as e:
        print(f"Error durante las operaciones {e}")

    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
            print("Conexion Cerrada")


guardarDataBase(correo, passwordUser)
