import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

from postulaciones import faltantesPerfil

load_dotenv()

MAX_VACANTES_INTERES = 5


def conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def separar_habilidades(texto):
    """"Python, SQL; Git" -> ["Python", "SQL", "Git"]."""
    return [h.strip() for h in str(texto or "").replace(";", ",").split(",") if h.strip()]


def perfilParaMejorar(cursor, correo):
    """Arma el perfil que se envía al agente, SIN datos personales (decisión 6).

    Igual al de las recomendaciones (#11), pero cada experiencia lleva su id para
    que el agente diga a cuál aplica cada cambio. No incluye nombre, edad,
    teléfono, correos, ubicación ni nombres de empresas o instituciones.
    """
    cursor.execute("SELECT Ocupacion FROM informacion_usuarios WHERE Correos = %s", (correo,))
    fila = cursor.fetchone()

    cursor.execute(
        "SELECT ID, Titulo_puesto, Sector_industria, Descripcion_funciones, Habilidades "
        "FROM Experiencia WHERE Correos_experiencia = %s ORDER BY Fecha_inicio DESC",
        (correo,),
    )
    experiencia = [
        {"id_experiencia": e[0], "cargo": e[1], "sector": e[2], "funciones": e[3], "habilidades": e[4]}
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


def vacantesDeInteres(cursor, correo):
    """Las vacantes que el usuario guardó (#16) o marcó «Me interesa» (#11), la más reciente primero."""
    consulta = (
        "SELECT v.Id_vacante, v.Cargo, v.Empresa, v.Descripcion, v.Requisitos, MAX(i.Fecha) AS Fecha "
        "FROM (SELECT Id_vacante_guardada AS Id, Fecha_guardada AS Fecha FROM Vacantes_guardadas "
        "WHERE Correos_guardada = %s "
        "UNION ALL SELECT Id_vacante_recomendacion, Fecha_decision FROM Recomendaciones "
        "WHERE Correos_recomendacion = %s AND Decision = 'Interesa') i "
        "JOIN Vacantes v ON v.Id_vacante = i.Id "
        "GROUP BY v.Id_vacante, v.Cargo, v.Empresa, v.Descripcion, v.Requisitos "
        "ORDER BY Fecha DESC, v.Id_vacante DESC LIMIT %s"
    )
    cursor.execute(consulta, (correo, correo, MAX_VACANTES_INTERES))
    columnas = [c[0] for c in cursor.description]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def consultarVacantesInteres(correo):
    """Retorna (True, lista) con las vacantes de interés que se compararán, o (False, mensaje)."""
    try:
        conexion = conectar()
        if conexion.is_connected():
            cursor = conexion.cursor()
            return True, vacantesDeInteres(cursor, correo)
        return False, "No se pudo conectar a la base de datos, intente de nuevo"
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudieron cargar tus vacantes de interés, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()


def generarSugerencias(correo):
    """Pide al agente sugerencias para mejorar el perfil según las vacantes de interés.

    Retorna (False, mensaje) si falla la base de datos, o (True, resultado) con:
      - "faltantes": lo que le falta al perfil (si no está vacío, no se llama al agente)
      - "sin_interes": True si no hay vacantes de interés (tampoco se llama al agente)
      - "sugerencias": lista de {"campo", "id_experiencia", "actual", "propuesta",
        "motivo", "vacantes", "seguro"}
      - "experiencias": {id: "Cargo en Empresa"} para mostrarlas (no va al agente)
      - "errores": mensajes del agente
    Nada se cambia en el perfil aquí (decisión 7): se cambia con aplicarSugerencia().
    """
    resultado = {"faltantes": [], "sin_interes": False, "sugerencias": [], "experiencias": {}, "errores": []}

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
        vacantes = vacantesDeInteres(cursor, correo)
        perfil = perfilParaMejorar(cursor, correo)
        cursor.execute(
            "SELECT ID, Titulo_puesto, Nombre_empresa FROM Experiencia WHERE Correos_experiencia = %s",
            (correo,),
        )
        resultado["experiencias"] = {e[0]: f"{e[1]} en {e[2]}" for e in cursor.fetchall()}
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo preparar tu perfil para el agente, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

    if not vacantes:
        resultado["sin_interes"] = True
        return True, resultado

    # El agente se importa aquí para que la aplicación arranque aunque falte la
    # clave de Anthropic; solo esta acción la necesita.
    from graph import sugerir_mejoras_cv

    estado = sugerir_mejoras_cv(perfil, vacantes)
    resultado["errores"] = estado.get("errores", [])
    resultado["sugerencias"] = estado.get("sugerencias", []) if not resultado["errores"] else []
    return True, resultado


def aplicarSugerencia(correo, campo, id_experiencia, texto):
    """Aplica al perfil el cambio que el usuario aceptó (con su texto, que pudo editar).

    - "ocupacion": reemplaza la ocupación de los datos básicos.
    - "funciones": reemplaza la descripción de funciones de esa experiencia.
    - "habilidades": agrega a esa experiencia las habilidades que todavía no tiene.
    Solo cambia datos del propio usuario. Retorna (True, mensaje) o (False, mensaje).
    """
    texto = (texto or "").strip()
    if not texto:
        return False, "La sugerencia quedó vacía: escríbela o descártala."
    try:
        conexion = conectar()
        if not conexion.is_connected():
            return False, "No se pudo conectar a la base de datos, intente de nuevo"
        cursor = conexion.cursor()

        if campo == "ocupacion":
            cursor.execute("SELECT COUNT(*) FROM informacion_usuarios WHERE Correos = %s", (correo,))
            if cursor.fetchone()[0] == 0:
                return False, "Primero guarda tus datos básicos en Mi perfil."
            cursor.execute(
                "UPDATE informacion_usuarios SET Ocupacion = %s WHERE Correos = %s", (texto, correo)
            )
            conexion.commit()
            return True, "Actualizaste tu ocupación."

        if campo not in ("funciones", "habilidades"):
            return False, "Esa sugerencia no se puede aplicar."
        cursor.execute(
            "SELECT Titulo_puesto, Habilidades FROM Experiencia "
            "WHERE ID = %s AND Correos_experiencia = %s",
            (id_experiencia, correo),
        )
        fila = cursor.fetchone()
        if fila is None:
            return False, "Esa experiencia ya no está en tu perfil."
        cargo, habilidades = fila

        if campo == "funciones":
            cursor.execute(
                "UPDATE Experiencia SET Descripcion_funciones = %s WHERE ID = %s AND Correos_experiencia = %s",
                (texto, id_experiencia, correo),
            )
            conexion.commit()
            return True, f"Actualizaste las funciones de «{cargo}»."

        actuales = separar_habilidades(habilidades)
        tiene = {h.lower() for h in actuales}
        nuevas = []
        for h in separar_habilidades(texto):
            if h.lower() not in tiene:
                tiene.add(h.lower())
                nuevas.append(h)
        if not nuevas:
            return False, f"«{cargo}» ya tiene esas habilidades."
        cursor.execute(
            "UPDATE Experiencia SET Habilidades = %s WHERE ID = %s AND Correos_experiencia = %s",
            (", ".join(actuales + nuevas), id_experiencia, correo),
        )
        conexion.commit()
        return True, f"Agregaste {', '.join(nuevas)} a las habilidades de «{cargo}»."
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo aplicar el cambio, intente de nuevo"
    finally:
        if "conexion" in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()
