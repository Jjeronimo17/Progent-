import login
import mysql.connector
from mysql.connector import Error


def añadirDatos(
    correo,
    nombre,
    edad,
    telefono,
    correo_contacto,
    experiencia,
    educacion,
    titulos,
    ubicacion,
    ocupacion,
    estudios=None,
):
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
            agregarInfo = "INSERT INTO informacion_usuarios VALUES(%s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s);"
            datos = (
                correo,
                nombre,
                edad,
                telefono,
                correo_contacto,
                experiencia,
                educacion,
                titulos,
                ubicacion,
                ocupacion,
                estudios,
            )
            cursor.execute(agregarInfo, datos)
            conexion.commit()

    except Error as e:
        print(f"Error durante las operaciones {e}")
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


añadirDatos(
    "jjaramila1@eafit.edu.co",
    "Jeronimo",
    18,
    "3023542198",
    "jeronimojaramillo2@gmail.com",
    "MYSQL, PYTHON Y C++",
    "Bachiller y estudiando en EAFIT",
    "Unicamente Bachiller (de momento)",
    "Barbosa",
    "Ingeniero de software",
    "Estudiando",
)
