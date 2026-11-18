import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()


def conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def perfilParaCompatibilidad(cursor, correo):
    """Arma el perfil que se envía al agente, SIN datos personales (decisión 6).

    Como el de las recomendaciones (#11), más los meses de cada experiencia y el nivel
    y estado de cada estudio, que sirven para comparar con los requisitos. No incluye
    nombre, edad, teléfono, correos, ubicación ni nombres de empresas o instituciones.
    """
    cursor.execute("SELECT Ocupacion FROM informacion_usuarios WHERE Correos = %s", (correo,))
    fila = cursor.fetchone()

    cursor.execute(
        "SELECT Titulo_puesto, Sector_industria, Descripcion_funciones, Habilidades, "
        "TIMESTAMPDIFF(MONTH, Fecha_inicio, COALESCE(Fecha_finalizacion, CURDATE())) "
        "FROM Experiencia WHERE Correos_experiencia = %s ORDER BY Fecha_inicio DESC",
        (correo,),
    )
    experiencia = [
        {"cargo": e[0], "sector": e[1], "funciones": e[2], "habilidades": e[3], "meses": e[4]}
        for e in cursor.fetchall()
    ]

    cursor.execute(
        "SELECT Titulo_Carrera_Grado, Campo_estudio, Nivel_educacion, Estado_estudio FROM Educacion "
        "WHERE Correos_educacion = %s ORDER BY Fecha_inicio DESC",
        (correo,),
    )
    educacion = [
        {"titulo": e[0], "campo": e[1], "nivel": e[2], "estado": e[3]} for e in cursor.fetchall()
    ]

    return {
        "ocupacion": fila[0] if fila else None,
        "experiencia": experiencia,
        "educacion": educacion,
    }


def faltaInformacion(perfil):
    """Lo que le falta al perfil para que la compatibilidad sea confiable."""
    faltan = []
    if not perfil["ocupacion"]:
        faltan.append("tu ocupación")
    if not perfil["experiencia"]:
        faltan.append("experiencia laboral")
    if not perfil["educacion"]:
        faltan.append("educación")
    return faltan


def calcularCompatibilidad(correo, id_vacante):
    """Pide al agente que compare el perfil con la vacante.

    Retorna (False, mensaje) si falla la base de datos, o (True, resultado) con:
      - "perfil_vacio": True si el perfil no tiene nada que comparar (no se llama al agente)
      - "falta": lo que le falta al perfil; si no está vacío, el resultado puede no ser preciso
      - "insuficiente": True si falta algo o el agente dijo que la información no alcanza
      - "criterios", "porcentaje", "nivel", "aproximado": lo calculado
      - "errores": mensajes del agente
    No se guarda nada: es una estimación para decidir antes de postularse.
    """
    resultado = {"perfil_vacio": False, "falta": [], "insuficiente": False, "criterios": [],
                 "porcentaje": 0, "nivel": None, "aproximado": False, "errores": []}
    try:
        conexion = conectar()
        if not conexion.is_connected():
            return False, "No se pudo conectar a la base de datos, intente de nuevo"
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT Id_vacante, Cargo, Descripcion, Requisitos, Modalidad FROM Vacantes WHERE Id_vacante = %s",
            (id_vacante,),
        )
        vacante = cursor.fetchone()
        cursor.close()
        cursor = conexion.cursor()
        perfil = perfilParaCompatibilidad(cursor, correo)
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo preparar tu perfil para el agente, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

    if vacante is None:
        return False, "Esta vacante ya no existe."
    resultado["falta"] = faltaInformacion(perfil)
    if len(resultado["falta"]) == 3:
        resultado["perfil_vacio"] = True
        return True, resultado

    # El agente se importa aquí para que la aplicación arranque aunque falte la
    # clave de Anthropic; solo esta acción la necesita.
    from graph import evaluar_compatibilidad_vacante

    estado = evaluar_compatibilidad_vacante(perfil, vacante)
    resultado["errores"] = estado.get("errores", [])
    if resultado["errores"]:
        return True, resultado
    for clave in ("criterios", "porcentaje", "nivel", "aproximado"):
        resultado[clave] = estado[clave]
    resultado["insuficiente"] = bool(resultado["falta"]) or not estado.get("informacion_suficiente", True)
    return True, resultado
