import os
from datetime import datetime
import mimetypes
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
    ubicacion,
    ocupacion,
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
            agregarInfo = (
                "INSERT INTO informacion_usuarios VALUES(%s, %s, %s, %s, %s,%s, %s);"
            )
            datos = (
                correo,
                nombre,
                edad,
                telefono,
                correo_contacto,
                ubicacion,
                ocupacion,
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
            verificarFecha = "SELECT TIMESTAMPDIFF(MONTH, %s, COALESCE(%s, CURDATE()))"
            datos = (fecha_inicio, fecha_finalizacion)
            cursor.execute(verificarFecha, datos)
            resultado = cursor.fetchone()
            if resultado[0] < 0:
                return (
                    False,
                    "La fecha de finalizacion no puede ser anterior a la fecha de inicio",
                )
            añadirExp = "INSERT INTO Experiencia(Correos_experiencia, Nombre_empresa, Sector_industria, Tamaño_empresa, Titulo_puesto, Nivel_seniority, Fecha_inicio, Fecha_finalizacion, Descripcion_funciones, Logros, Habilidades, Ubicacion_empresa, Tipo_contrato, Modalidad_trabajo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
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
        return False, "No se pudo añadir la experiencia al perfil, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def añadirEducacion(
    correo,
    institucion_educativa,
    tipo_institucion,
    titulo_carrera_grado,
    nivel_educacion,
    campo_estudio,
    fecha_inicio,
    estado_estudio,
    logros,
    fecha_final=None,
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
            verificarFecha = "SELECT TIMESTAMPDIFF(MONTH, %s, COALESCE(%s, CURDATE()))"
            datos = (fecha_inicio, fecha_final)
            cursor.execute(verificarFecha, datos)
            resultado = cursor.fetchone()
            if resultado[0] < 0:
                return (
                    False,
                    "La fecha de finalizacion no puede ser anterior a la de inicio",
                )
            añadirEdu = "INSERT INTO Educacion(Correos_educacion, Institucion_educativa, Tipo_institucion, Titulo_Carrera_Grado, Nivel_educacion, Campo_estudio, Fecha_inicio, Fecha_final, Estado_estudio, Logros) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            parametros = (
                correo,
                institucion_educativa,
                tipo_institucion,
                titulo_carrera_grado,
                nivel_educacion,
                campo_estudio,
                fecha_inicio,
                fecha_final,
                estado_estudio,
                logros,
            )
            cursor.execute(añadirEdu, parametros)
            conexion.commit()
            return True, "Se añadio su educacion de manera correcta a su perfil"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo añadir la educacion a su perfil, vuelva a intentar"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def añadirDatosExtraidos(correo, datos):
    verificar_perfil = "SELECT * FROM informacion_usuarios WHERE Correos = %s"
    verificar_experiencia = "SELECT * FROM Experiencia WHERE Correos_experiencia = %s"
    verificar_educacion = "SELECT * FROM Educacion WHERE Correos_educacion = %s"
    verificar_perfil_datos = (correo,)
    verificar_experiencia_datos = (correo,)
    verificar_educacion_datos = (correo,)
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
            cursor.execute(verificar_perfil, verificar_perfil_datos)
            resultado_perfil = cursor.fetchone()
            cursor.execute(verificar_experiencia, verificar_experiencia_datos)
            resultado_experiencia = cursor.fetchall()
            cursor.execute(verificar_educacion, verificar_educacion_datos)
            resultado_educacion = cursor.fetchall()
            if (resultado_perfil) or (resultado_educacion) or (resultado_experiencia):
                return False, "Ya tienes un perfil creado"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
    nombre = datos["nombre_completo"]
    titulo = datos["titular"]
    correo_contacto = datos["contacto"]["correo"]
    telefono_contacto = datos["contacto"]["telefono"]
    ubicacion = datos["contacto"]["ciudad"]
    lenguas = []
    for i in datos["idiomas"]:
        lenguas.append(i["idioma"])
    habilidades_tecnicas = ", ".join(datos["habilidades"]) + ", " + ", ".join(lenguas)
    añadir_datos, mensajeDat = añadirDatos(
        correo,
        nombre,
        None,
        telefono_contacto,
        correo_contacto,
        ubicacion,
        titulo,
    )
    if not añadir_datos:
        return False, "Ocurrio un fallo al intentar cargar la informacion a tu perfil"
    for experiencia in datos["experiencia"]:
        formato = "%Y-%m-%d"
        if experiencia["actual"] == True:
            fecha_final = None
            fecha_final_formateada = None
        else:
            fecha_final = experiencia["fecha_fin"]
            fecha_final_formateada = datetime.strptime(fecha_final, formato)

        fecha_inicio = experiencia["fecha_inicio"]
        fecha_inicio_formateada = datetime.strptime(fecha_inicio, formato)
        añadir_experiencia = añadirExperiencia(
            correo,
            experiencia["empresa"],
            None,
            None,
            experiencia["cargo"],
            None,
            fecha_inicio_formateada,
            experiencia["descripcion"],
            None,
            habilidades_tecnicas,
            None,
            None,
            None,
            fecha_final_formateada,
        )
        if not añadir_experiencia:
            return False, "No se pudo añadir correctamente la experiencia(s) al perfil"
    for educacion in datos["educacion"]:
        formatoEducacion = "%Y-%m-%d"
        if educacion["en_curso"] == True:
            fecha_final_educacion = None
            fecha_final_educacion_formateada = None
            estado_estudio = "Cursando"
        else:
            fecha_final_educacion = educacion["fecha_fin"]
            fecha_final_educacion_formateada = datetime.strptime(
                fecha_final_educacion, formatoEducacion
            )
            estado_estudio = "Graduado"
        fecha_inicio_educacion = educacion["fecha_inicio"]
        fecha_inicio_educacion_formateada = datetime.strptime(
            fecha_inicio_educacion, formatoEducacion
        )
        añadir_educacion, mensajeEdu = añadirEducacion(
            correo,
            educacion["institucion"],
            None,
            educacion["titulo"],
            None,
            None,
            fecha_inicio_educacion_formateada,
            estado_estudio,
            None,
            fecha_final_educacion_formateada,
        )
        if not añadir_educacion:
            return False, "No se pudo añadir la educacion al perfil"
        if añadir_educacion and añadir_experiencia and añadir_datos:
            return True, "Datos agregados correctamente"


def guardarArchivos(correo, nombre_archivo, bytes):
    tipo_MIME, _ = mimetypes.guess_type(nombre_archivo)
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
            insertar = "INSERT INTO archivos_usuarios(Correos_usuarios, nombre_archivo, tipo, archivo_bytes) VALUES(%s, %s, %s, %s)"
            datosInsertar = (correo, nombre_archivo, tipo_MIME, bytes)
            cursor.execute(insertar, datosInsertar)
            conexion.commit()
            return True, "Se guardo correctamente su archivo en su perfil"

    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo guardar el archivo en su perfil"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def actualizarArchivo(correo, nombre_archivo, bytes):
    tipo_MIME, _ = mimetypes.guess_type(nombre_archivo)
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
            traerRegistros = (
                "SELECT * FROM archivos_usuarios WHERE Correos_usuarios = %s"
            )
            dato_traer_registros = (correo,)
            cursor.execute(traerRegistros, dato_traer_registros)
            resultado_registros = cursor.fetchone()
            nombre_archivo_original = resultado_registros[0]
            tipo_archivo_original = resultado_registros[1]
            bytes_originales = resultado_registros[2]
            if nombre_archivo != nombre_archivo_original:
                actualizacion_nombre = "UPDATE archivos_usuarios SET nombre_archivo = %s WHERE Correos_usuarios = %s"
                datos_actualizar_nombre = (nombre_archivo, correo)
                cursor.execute(actualizacion_nombre, datos_actualizar_nombre)

            if tipo_MIME != tipo_archivo_original:
                actualizacion_tipo = (
                    "UPDATE archivos_usuarios SET tipo = %s WHERE Correos_usuarios = %s"
                )
                datos_actualizar_tipo = (tipo_MIME, correo)
                cursor.execute(actualizacion_tipo, datos_actualizar_tipo)
            if bytes != bytes_originales:
                actualizacion_bytes = "UPDATE archivos_usuarios SET archivo_bytes = %s WHERE Correos_usuarios = %s"
                datos_actualizar_bytes = (bytes, correo)
                cursor.execute(actualizacion_bytes, datos_actualizar_bytes)
            conexion.commit()
            return True, "Se cargo el nuevo archivo a su perfil"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo cargar el nuevo archivo a su perfil"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarArchivo(correo):
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
            traer_archivo = (
                "SELECT * FROM archivos_usuarios WHERE Correos_usuarios = %s"
            )
            dato_traer_archivo = (correo,)
            cursor.execute(traer_archivo, dato_traer_archivo)
            resultado_traer_archivo = cursor.fetchone()
            return True, resultado_traer_archivo
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo cargar el archivo guardado en su perfil"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarEducacion(correo):
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
            consultarEdu = "SELECT * FROM Educacion WHERE Correos_educacion = %s"
            parametro = (correo,)
            cursor.execute(consultarEdu, parametro)
            resultado = cursor.fetchall()
            return True, resultado
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return (
            False,
            "No se pudo obtener la educacion añadida a su perfil, vuelva a intentar",
        )
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
            consultarExp = "SELECT * FROM Experiencia WHERE Correos_experiencia = %s"
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
    ubicacion,
    ocupacion,
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
            recuperarValores = "SELECT Nombre, Edad, Telefono, Correo_contacto,Ubicacion, Ocupacion FROM informacion_usuarios WHERE Correos = %s;"
            dato = (correo,)
            cursor.execute(recuperarValores, dato)
            resultadoConsulta = cursor.fetchone()
            nombreOriginal = resultadoConsulta[0]
            edadOriginal = resultadoConsulta[1]
            telefonoOriginal = resultadoConsulta[2]
            correo_contactoOriginal = resultadoConsulta[3]
            ubicacionOriginal = resultadoConsulta[4]
            ocupacionOriginal = resultadoConsulta[5]
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
