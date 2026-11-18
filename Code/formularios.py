import io
import os

import mysql.connector
from docx import Document
from dotenv import load_dotenv
from mysql.connector import Error
from pypdf import PdfReader

from documentos import validarDocumento
from recomendaciones import perfilParaRecomendar

load_dotenv()

MAX_CARACTERES = 15000


def conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def leerFormulario(nombre_archivo, datos):
    """Saca el texto de un formulario en PDF o Word. Retorna (True, texto) o (False, mensaje)."""
    valido, tipo = validarDocumento(nombre_archivo, datos, max_bytes=5 * 1024 * 1024)
    if not valido:
        return False, tipo
    try:
        if nombre_archivo.lower().endswith(".pdf"):
            texto = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(datos)).pages)
        else:
            documento = Document(io.BytesIO(datos))
            partes = [p.text for p in documento.paragraphs]
            partes += [c.text for t in documento.tables for f in t.rows for c in f.cells]
            texto = "\n".join(partes)
    except Exception as e:  # archivo dañado: pypdf y python-docx lanzan errores distintos
        print(f"Fallo al leer el formulario {e}")
        return False, "No se pudo leer el archivo. Prueba pegando el texto del formulario."
    texto = texto.strip()
    if len(texto) < 10:
        return False, "El archivo no tiene texto seleccionable. Prueba pegando el texto del formulario."
    return True, texto


def datosPersonales(cursor, correo):
    """Datos personales del perfil. Se usan SOLO aquí, nunca se envían al agente."""
    cursor.execute(
        "SELECT Nombre, Correo_contacto, Telefono, Ubicacion, Edad "
        "FROM informacion_usuarios WHERE Correos = %s",
        (correo,),
    )
    fila = cursor.fetchone() or (None,) * 5
    claves = ["nombre", "correo", "telefono", "ciudad", "edad"]
    return {c: (str(v) if v is not None else "") for c, v in zip(claves, fila)}


def generarRespuestas(correo, id_postulacion, texto_formulario):
    """Pide al agente que llene el formulario y completa localmente los datos personales.

    Retorna (False, mensaje) o (True, {"campos": [...], "errores": [...]}) donde cada campo es
    {"pregunta", "respuesta", "estado": "seguro"|"dudoso"|"manual"|"personal", "nota"}.
    Nada se guarda aquí (decisión 7): se guarda con guardarRespuestas() al confirmar.
    """
    texto_formulario = (texto_formulario or "").strip()[:MAX_CARACTERES]
    if len(texto_formulario) < 10:
        return False, "Pega el texto del formulario o sube el archivo antes de procesarlo."
    try:
        conexion = conectar()
        if not conexion.is_connected():
            return False, "No se pudo conectar a la base de datos, intente de nuevo"
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Postulaciones WHERE Id_postulacion = %s AND Correos_postulacion = %s",
            (id_postulacion, correo),
        )
        if cursor.fetchone()[0] == 0:
            return False, "Esta postulación no existe."
        perfil = perfilParaRecomendar(cursor, correo)
        personales = datosPersonales(cursor, correo)
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo preparar tu perfil para el agente, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

    # Se importa aquí para que la aplicación arranque aunque falte la clave de Anthropic.
    from graph import completar_formulario

    estado = completar_formulario(texto_formulario, perfil)
    if estado.get("errores"):
        return True, {"campos": [], "errores": estado["errores"]}

    campos = []
    for c in estado["campos"]:
        if c["tipo"] == "dato_personal":
            valor = personales.get(c["dato_personal"], "")
            if valor:
                campos.append({"pregunta": c["pregunta"], "respuesta": valor, "estado": "personal", "nota": ""})
            else:
                campos.append({"pregunta": c["pregunta"], "respuesta": "", "estado": "manual",
                               "nota": "Tu perfil no tiene este dato."})
        elif c["tipo"] == "respuesta":
            campos.append({"pregunta": c["pregunta"], "respuesta": c["respuesta"],
                           "estado": "seguro" if c["seguro"] else "dudoso", "nota": c["nota"]})
        else:
            campos.append({"pregunta": c["pregunta"], "respuesta": "", "estado": "manual", "nota": c["nota"]})
    return True, {"campos": campos, "errores": []}


def guardarRespuestas(correo, id_postulacion, respuestas):
    """Guarda las respuestas confirmadas [(pregunta, respuesta), ...]; reemplaza las anteriores."""
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
                "DELETE FROM Respuestas_formulario WHERE Id_postulacion_respuesta = %s", (id_postulacion,)
            )
            cursor.executemany(
                "INSERT INTO Respuestas_formulario(Id_postulacion_respuesta, Orden, Pregunta, Respuesta) "
                "VALUES (%s, %s, %s, %s)",
                [(id_postulacion, i, p, r) for i, (p, r) in enumerate(respuestas, start=1)],
            )
            conexion.commit()
            return True, f"Guardaste {len(respuestas)} respuestas. Cópialas en el portal de la empresa."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron guardar las respuestas, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarRespuestas(correo, id_postulacion):
    """Retorna (True, lista de {Pregunta, Respuesta, Fecha_confirmacion}) o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = (
                "SELECT r.Pregunta, r.Respuesta, r.Fecha_confirmacion FROM Respuestas_formulario r "
                "JOIN Postulaciones p ON p.Id_postulacion = r.Id_postulacion_respuesta "
                "WHERE r.Id_postulacion_respuesta = %s AND p.Correos_postulacion = %s ORDER BY r.Orden"
            )
            cursor.execute(consulta, (id_postulacion, correo))
            return True, cursor.fetchall()
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron cargar tus respuestas, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
