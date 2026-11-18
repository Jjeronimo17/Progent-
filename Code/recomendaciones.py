import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

from postulaciones import faltantesPerfil
from vacantes import escaparComodines

load_dotenv()

MAX_CANDIDATAS = 20


def conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def consultarCriterios(correo):
    """Retorna (True, diccionario o None) con los criterios del usuario, o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = (
                "SELECT Cargo_deseado, Modalidad, Ciudad FROM Criterios_busqueda "
                "WHERE Correos_criterios = %s"
            )
            cursor.execute(consulta, (correo,))
            return True, cursor.fetchone()
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron cargar tus criterios, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def guardarCriterios(correo, cargo_deseado, modalidad, ciudad):
    """Crea o actualiza los criterios del usuario. Retorna (True, mensaje) o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            guardar = (
                "INSERT INTO Criterios_busqueda(Correos_criterios, Cargo_deseado, Modalidad, Ciudad) "
                "VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE Cargo_deseado = VALUES(Cargo_deseado), "
                "Modalidad = VALUES(Modalidad), Ciudad = VALUES(Ciudad)"
            )
            cursor.execute(guardar, (correo, cargo_deseado, modalidad, ciudad))
            conexion.commit()
            return True, "Tus criterios quedaron guardados."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron guardar tus criterios, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def perfilParaRecomendar(cursor, correo):
    """Arma el perfil que se envía al agente, SIN datos personales (decisión 6).

    Solo incluye la ocupación, la experiencia (cargo, sector, funciones y
    habilidades) y la educación (título y campo). No incluye nombre, edad,
    teléfono, correos, ubicación ni nombres de empresas o instituciones.
    """
    cursor.execute("SELECT Ocupacion FROM informacion_usuarios WHERE Correos = %s", (correo,))
    fila = cursor.fetchone()

    cursor.execute(
        "SELECT Titulo_puesto, Sector_industria, Descripcion_funciones, Habilidades "
        "FROM Experiencia WHERE Correos_experiencia = %s ORDER BY Fecha_inicio DESC",
        (correo,),
    )
    experiencia = [
        {"cargo": e[0], "sector": e[1], "funciones": e[2], "habilidades": e[3]}
        for e in cursor.fetchall()
    ]

    cursor.execute(
        "SELECT Titulo_Carrera_Grado, Campo_estudio FROM Educacion "
        "WHERE Correos_educacion = %s ORDER BY Fecha_inicio DESC",
        (correo,),
    )
    educacion = [{"titulo": e[0], "campo": e[1]} for e in cursor.fetchall()]

    return {
        "ocupacion": fila[0] if fila else None,
        "experiencia": experiencia,
        "educacion": educacion,
    }


def vacantesCandidatas(cursor, correo, ciudad=None):
    """Vacantes abiertas que el usuario no ha decidido ni a las que se ha postulado.

    Si hay ciudad, solo entran las de esa ciudad o las remotas.
    """
    consulta = (
        "SELECT Id_vacante, Cargo, Empresa, Ubicacion, Descripcion, Requisitos, "
        "Fecha_publicacion FROM Vacantes WHERE Estado = 'Abierta' "
        "AND Id_vacante NOT IN (SELECT Id_vacante_recomendacion FROM Recomendaciones "
        "WHERE Correos_recomendacion = %s) "
        "AND Id_vacante NOT IN (SELECT Id_vacante_postulacion FROM Postulaciones "
        "WHERE Correos_postulacion = %s)"
    )
    parametros = (correo, correo)
    if ciudad:
        consulta += " AND (Ubicacion LIKE %s OR Ubicacion = 'Remoto')"
        parametros += (f"%{escaparComodines(ciudad)}%",)
    consulta += " ORDER BY Fecha_publicacion DESC, Id_vacante DESC LIMIT %s"
    parametros += (MAX_CANDIDATAS,)
    cursor.execute(consulta, parametros)
    columnas = [c[0] for c in cursor.description]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def generarRecomendaciones(correo):
    """Pide recomendaciones al agente para el usuario.

    Retorna (False, mensaje) si falla la base de datos, o (True, resultado) con:
      - "faltantes": lo que le falta al perfil (si no está vacío, no se llama al agente)
      - "sin_candidatas": True si no hay vacantes para recomendar
      - "recomendaciones": lista de {"vacante", "motivo", "seguro"}
      - "errores": mensajes del agente
    Lo que devuelve el agente NO se guarda aquí (decisión 7): se guarda cuando el
    usuario lo confirma o lo descarta con guardarDecision().
    """
    resultado = {"faltantes": [], "sin_candidatas": False, "recomendaciones": [], "errores": []}

    exito, faltantes = faltantesPerfil(correo)
    if not exito:
        return False, faltantes
    if faltantes:
        resultado["faltantes"] = faltantes
        return True, resultado

    try:
        conexion = conectar()
        if not conexion.is_connected():
            return False, "No se pudo conectar a la base de datos, intente de nuevo"
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT Cargo_deseado, Modalidad, Ciudad FROM Criterios_busqueda "
            "WHERE Correos_criterios = %s",
            (correo,),
        )
        criterios = cursor.fetchone() or (None, None, None)
        perfil = perfilParaRecomendar(cursor, correo)
        candidatas = vacantesCandidatas(cursor, correo, criterios[2])
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo preparar tu perfil para el agente, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

    if not candidatas:
        resultado["sin_candidatas"] = True
        return True, resultado

    # El agente se importa aquí para que la aplicación arranque aunque falte la
    # clave de Anthropic; solo esta acción la necesita.
    from graph import recomendar_vacantes

    # La ciudad solo se usó para filtrar: no se envía al agente.
    preferencias = {"cargo_deseado": criterios[0], "modalidad": criterios[1]}
    estado = recomendar_vacantes(perfil, preferencias, candidatas)
    resultado["errores"] = estado.get("errores", [])
    resultado["recomendaciones"] = estado.get("recomendaciones", []) if not resultado["errores"] else []
    return True, resultado


def guardarDecision(correo, id_vacante, decision, motivo):
    """Guarda si el usuario confirmó ('Interesa') o descartó ('Descartada') una recomendación."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            insertar = (
                "INSERT INTO Recomendaciones(Correos_recomendacion, Id_vacante_recomendacion, "
                "Decision, Motivo) VALUES (%s, %s, %s, %s)"
            )
            cursor.execute(insertar, (correo, id_vacante, decision, motivo))
            conexion.commit()
            if decision == "Interesa":
                return True, "La marcaste como de interés."
            return True, "La descartaste; no te la volveré a recomendar."
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        if e.errno == 1062:
            return False, "Ya habías respondido a esta recomendación."
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo guardar tu respuesta, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def consultarDeInteres(correo):
    """Retorna (True, lista) con las vacantes que el usuario marcó de interés, o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
            consulta = (
                "SELECT v.Id_vacante, v.Cargo, v.Empresa, v.Ubicacion, v.Estado, "
                "r.Motivo, r.Fecha_decision FROM Recomendaciones r "
                "JOIN Vacantes v ON v.Id_vacante = r.Id_vacante_recomendacion "
                "WHERE r.Correos_recomendacion = %s AND r.Decision = 'Interesa' "
                "ORDER BY r.Fecha_decision DESC, r.Id_recomendacion DESC"
            )
            cursor.execute(consulta, (correo,))
            return True, cursor.fetchall()
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron cargar tus vacantes de interés, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
