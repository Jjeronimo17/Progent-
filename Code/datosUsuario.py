import os
import login
import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()


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
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )
        if conexion.is_connected():
            cursor = conexion.cursor()
            agregarInfo = "INSERT INTO informacion_usuarios VALUES(%s, %s, %s, %s, %s,%s, %s, %s, %s);"
            datos = (
                correo,
                nombre,
                edad,
                telefono,
                correo_contacto,
                titulos,
                ubicacion,
                ocupacion,
                estudios,
            )
            cursor.execute(agregarInfo, datos)
            conexion.commit()
            return True, "Informacion de perfil añadida correctamente"

    except Error as e:
        if e.errno == 1048 or e.errno == 1366:
            return (False, e.msg)
        else:
            return (False, "No se pudo completar el llenado de perfil")

    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def añadirExperiencia(
    correo,
    nombre_empresa,
    sector_industria,
    tamaño_empresa,
    titulo_puesto,
    nivel_seniority,
    fecha_inicio,
    descripcion_funciones,
    logros,
    habilidades,
    ubicacion_empresa,
    tipo_contrato,
    modalidad_trabajo,
    fecha_finalizacion=None,
):
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
            añadirExp = "INSERT INTO Experiencia VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            valoresAñadir = (
                correo,
                nombre_empresa,
                sector_industria,
                tamaño_empresa,
                titulo_puesto,
                nivel_seniority,
                fecha_inicio,
                fecha_finalizacion,
                descripcion_funciones,
                logros,
                habilidades,
                ubicacion_empresa,
                tipo_contrato,
                modalidad_trabajo,
            )
            cursor.execute(añadirExp, valoresAñadir)
            conexion.commit()
            return True, "Experiencia añadida correctamente al perfil"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarExperiencia(correo):
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
            consultarExp = "SELECT * FROM Experiencia WHERE Correos = %s"
            parametro = (correo,)
            cursor.execute(consultarExp, parametro)
            resultado = cursor.fetchall()
            return True, resultado
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo cargar la experiencia en el perfil, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarDatos(correo):
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
            consultarInfo = "SELECT * FROM informacion_usuarios WHERE Correos = %s"
            dato = (correo,)
            cursor.execute(consultarInfo, dato)
            resultado = cursor.fetchone()
            return True, resultado
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo cargar el perfil correctamente"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def actualizarPerfil(
    correo,
    nombre,
    edad,
    telefono,
    correo_contacto,
    titulos,
    ubicacion,
    ocupacion,
    estudios=None,
):
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
            recuperarValores = "SELECT Nombre, Edad, Telefono, Correo_contacto, Titulos, Ubicacion, Ocupacion, Estudios FROM informacion_usuarios WHERE Correos = %s;"
            dato = (correo,)
            cursor.execute(recuperarValores, dato)
            resultadoConsulta = cursor.fetchone()
            nombreOriginal = resultadoConsulta[0]
            edadOriginal = resultadoConsulta[1]
            telefonoOriginal = resultadoConsulta[2]
            correo_contactoOriginal = resultadoConsulta[3]
            titulosOriginal = resultadoConsulta[6]
            ubicacionOriginal = resultadoConsulta[7]
            ocupacionOriginal = resultadoConsulta[8]
            estudiosOriginal = resultadoConsulta[9]
            Cambios = []
            if nombre != nombreOriginal:
                consulta = (
                    "UPDATE informacion_usuarios SET Nombre = %s WHERE Correos = %s"
                )
                datosC = (nombre, correo)
                cursor.execute(consulta, datosC)
                Cambios.append("Nombre")
            if int(edad) != edadOriginal:
                consulta2 = (
                    "UPDATE informacion_usuarios SET Edad = %s WHERE Correos = %s"
                )
                datos2 = (edad, correo)
                cursor.execute(consulta2, datos2)
                Cambios.append("Edad")
            if telefono != telefonoOriginal:
                consulta3 = (
                    "UPDATE informacion_usuarios SET Telefono = %s WHERE Correos = %s"
                )
                datos3 = (telefono, correo)
                cursor.execute(consulta3, datos3)
                Cambios.append("Telefono")
            if correo_contacto != correo_contactoOriginal:
                consulta4 = "UPDATE informacion_usuarios SET Correo_contacto = %s WHERE Correos = %s"
                datos4 = (correo_contacto, correo)
                cursor.execute(consulta4, datos4)
                Cambios.append("Correo de Contacto")
            if titulos != titulosOriginal:
                consulta5 = (
                    "UPDATE informacion_usuarios SET Titulos = %s WHERE Correos = %s"
                )
                datos5 = (titulos, correo)
                cursor.execute(consulta5, datos5)
                Cambios.append("Titulos")
            if ubicacion != ubicacionOriginal:
                consulta6 = (
                    "UPDATE informacion_usuarios SET Ubicacion = %s WHERE Correos = %s"
                )
                datos6 = (ubicacion, correo)
                cursor.execute(consulta6, datos6)
                Cambios.append("Ubicacion")
            if ocupacion != ocupacionOriginal:
                consulta7 = (
                    "UPDATE informacion_usuarios SET Ocupacion = %s WHERE Correos = %s"
                )
                datos7 = (ocupacion, correo)
                cursor.execute(consulta7, datos7)
                Cambios.append("Ocupacion")
            if (estudios == "" and estudiosOriginal != None) or (
                estudios != "" and estudiosOriginal == None
            ):
                consulta8 = (
                    "UPDATE informacion_usuarios SET Estudios = %s WHERE Correos = %s"
                )
                datos8 = (estudios, correo)
                cursor.execute(consulta8, datos8)
                Cambios.append("Estudios")
            conexion.commit()
            if not Cambios:
                return False, "No hubieron cambios para guardar"
            else:
                listaCambios = " ".join(Cambios)
                return True, f"Se actualizaron los siguientes campos {listaCambios}"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
