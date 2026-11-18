import os
from datetime import datetime

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

from entrevistas import ESTADOS_SIN_RECORDATORIO, cuandoEs

load_dotenv()


def conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def procesosActivos(cursor, correo):
    """Postulaciones que siguen en curso (no rechazadas ni retiradas), con lo que sirve para priorizar."""
    cursor.execute(
        "SELECT p.Id_postulacion, v.Cargo, v.Empresa, p.Estado, v.Estado AS Estado_vacante, "
        "DATEDIFF(CURDATE(), DATE(p.Fecha_postulacion)) AS Dias_postulado, "
        "DATEDIFF(CURDATE(), DATE(p.Fecha_actualizacion)) AS Dias_sin_cambios, e.Fecha_entrevista "
        "FROM Postulaciones p JOIN Vacantes v ON v.Id_vacante = p.Id_vacante_postulacion "
        "LEFT JOIN Entrevistas e ON e.Id_postulacion_entrevista = p.Id_postulacion "
        "WHERE p.Correos_postulacion = %s AND p.Estado NOT IN (%s, %s) "
        "ORDER BY p.Fecha_postulacion DESC, p.Id_postulacion DESC",
        (correo, *ESTADOS_SIN_RECORDATORIO),
    )
    columnas = [c[0] for c in cursor.description]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def procesoParaAgente(proceso, ahora):
    """Lo que recibe el agente de cada proceso. Ningún dato personal (decisión 6)."""
    entrevista = proceso["Fecha_entrevista"]
    if entrevista is None:
        cuando = None
    elif entrevista >= ahora:
        cuando = cuandoEs(entrevista, ahora)
    else:
        cuando = "ya pasó y no se actualizó"
    return {
        "id_proceso": proceso["Id_postulacion"],
        "cargo": proceso["Cargo"],
        "etapa": proceso["Estado"],
        "dias_desde_postulacion": proceso["Dias_postulado"],
        "dias_sin_cambios": proceso["Dias_sin_cambios"],
        "proxima_entrevista": cuando,
        "vacante_abierta": proceso["Estado_vacante"] == "Abierta",
    }


def generarPrioridades(correo):
    """Pide al agente un orden sugerido para atender los procesos activos.

    Retorna (False, mensaje) si falla la base de datos, o (True, resultado) con:
      - "procesos": {id: proceso} de los procesos activos (para mostrarlos)
      - "orden": lista de {"id_proceso", "motivo", "seguro"}; vacía si hay menos de 2
        procesos activos, porque no hay nada que ordenar (no se llama al agente)
      - "resumen" y "errores": lo que dijo el agente
    No cambia nada en las postulaciones.
    """
    resultado = {"procesos": {}, "orden": [], "resumen": "", "errores": []}
    try:
        conexion = conectar()
        if not conexion.is_connected():
            return False, "No se pudo conectar a la base de datos, intente de nuevo"
        cursor = conexion.cursor()
        activos = procesosActivos(cursor, correo)
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron revisar tus procesos, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

    resultado["procesos"] = {p["Id_postulacion"]: p for p in activos}
    if len(activos) < 2:
        return True, resultado

    # El agente se importa aquí para que la aplicación arranque aunque falte la
    # clave de Anthropic; solo esta acción la necesita.
    from graph import sugerir_prioridades

    ahora = datetime.now()
    estado = sugerir_prioridades([procesoParaAgente(p, ahora) for p in activos])
    resultado["errores"] = estado.get("errores", [])
    if not resultado["errores"]:
        resultado["orden"] = estado["orden"]
        resultado["resumen"] = estado.get("resumen", "")
    return True, resultado
