"""Importar el perfil desde un archivo con el agente de extracción (historias #4, #5 y #6).

El agente de graph.py lee el archivo y propone el perfil. Nada se guarda hasta que el
usuario lo revisa y lo confirma (decisión 7); entonces se guarda con
datosUsuario.añadirDatosExtraidos, que solo llena un perfil vacío.
"""

import os
from datetime import datetime

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

from datosUsuario import añadirDatosExtraidos
from documentos import validarDocumento

load_dotenv()

MAX_BYTES = 5 * 1024 * 1024
FORMATO_FECHA = "%Y-%m-%d"


def conectar():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def tienePerfil(correo):
    """True si el usuario ya tiene datos básicos, experiencia o educación."""
    conexion, cursor = conectar(), None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT (SELECT COUNT(*) FROM informacion_usuarios WHERE Correos = %s) "
            "+ (SELECT COUNT(*) FROM Experiencia WHERE Correos_experiencia = %s) "
            "+ (SELECT COUNT(*) FROM Educacion WHERE Correos_educacion = %s)",
            (correo, correo, correo),
        )
        return cursor.fetchone()[0] > 0
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def _texto(valor):
    return str(valor).strip() if valor is not None else ""


def _fecha(valor):
    """La fecha del agente si viene como AAAA-MM-DD; si no, vacía (el usuario la escribe)."""
    texto = _texto(valor)[:10]
    try:
        datetime.strptime(texto, FORMATO_FECHA)
        return texto
    except ValueError:
        return ""


def borradorDesdePerfil(perfil, correo_cuenta):
    """Pasa la propuesta del agente a un borrador que el usuario puede revisar y editar."""
    contacto = perfil.get("contacto") or {}
    return {
        "nombre": _texto(perfil.get("nombre_completo")),
        "titular": _texto(perfil.get("titular")),
        # El PDF de LinkedIn no trae el correo: se propone el de la cuenta.
        "correo": _texto(contacto.get("correo")) or correo_cuenta,
        "telefono": _texto(contacto.get("telefono")),
        "ciudad": _texto(contacto.get("ciudad")),
        "experiencia": [
            {
                "cargo": _texto(e.get("cargo")),
                "empresa": _texto(e.get("empresa")),
                "fecha_inicio": _fecha(e.get("fecha_inicio")),
                "fecha_fin": _fecha(e.get("fecha_fin")),
                "actual": e.get("actual") is True,
                "descripcion": _texto(e.get("descripcion")),
            }
            for e in perfil.get("experiencia") or []
            if isinstance(e, dict)
        ],
        "educacion": [
            {
                "titulo": _texto(e.get("titulo")),
                "institucion": _texto(e.get("institucion")),
                "fecha_inicio": _fecha(e.get("fecha_inicio")),
                "fecha_fin": _fecha(e.get("fecha_fin")),
                "en_curso": e.get("en_curso") is True,
            }
            for e in perfil.get("educacion") or []
            if isinstance(e, dict)
        ],
        "habilidades": [_texto(h) for h in perfil.get("habilidades") or [] if _texto(h)],
        "idiomas": [
            {"idioma": _texto(i.get("idioma")), "nivel": _texto(i.get("nivel")) or None}
            for i in perfil.get("idiomas") or []
            if isinstance(i, dict) and _texto(i.get("idioma"))
        ],
        "dudosos": [_texto(c) for c in perfil.get("campos_dudosos") or [] if _texto(c)],
    }


def extraerPerfil(correo, nombre_archivo, datos, origen):
    """Lee el archivo con el agente y devuelve el borrador del perfil para revisarlo.

    origen: "cv" (hoja de vida en PDF o Word) o "linkedin" (PDF del perfil de LinkedIn).
    Retorna (False, mensaje) o (True, resultado) con:
      - "sin_texto": True si el PDF no tiene texto (por ejemplo, un escaneo)
      - "borrador": la propuesta del agente, con "dudosos"
    """
    if origen == "linkedin" and not nombre_archivo.lower().endswith(".pdf"):
        return False, (
            "Sube el PDF de tu perfil de LinkedIn: en LinkedIn abre tu perfil, "
            "elige «Más» y luego «Guardar en PDF»."
        )
    valido, tipo_mime = validarDocumento(nombre_archivo, datos, max_bytes=MAX_BYTES)
    if not valido:
        return False, tipo_mime

    try:
        if tienePerfil(correo):
            return False, (
                "Ya tienes datos en tu perfil. La importación solo llena un perfil vacío; "
                "edita el tuyo en «Llenar mi perfil manualmente»."
            )
    except Error as e:
        print(f"Fallo en las operaciones de arriba {e}")
        return False, "No se pudo revisar tu perfil, intente de nuevo"

    # El agente se importa aquí para que la aplicación arranque aunque falte la
    # clave de Anthropic; solo esta acción la necesita.
    from graph import extraer_perfil_archivo

    tipo = "docx" if nombre_archivo.lower().endswith(".docx") else "pdf"
    try:
        estado = extraer_perfil_archivo(datos, tipo, origen)
    except Exception as e:
        print(f"Fallo del agente de extracción {e}")
        return False, "El agente no respondió. Vuelve a cargar el archivo para intentarlo de nuevo."

    errores = estado.get("errores") or []
    if any(e.startswith("El PDF no tiene texto") for e in errores):
        return True, {"sin_texto": True, "borrador": None}
    if errores:
        print("Errores del agente de extracción:", errores)
        return False, (
            "El agente no pudo leer bien el archivo. Vuelve a cargarlo para intentarlo de "
            "nuevo o llena tu perfil manualmente."
        )
    return True, {"sin_texto": False, "borrador": borradorDesdePerfil(estado["perfil"], correo)}


def erroresBorrador(borrador):
    """Lo que falta o está mal antes de guardar. Lista vacía si se puede guardar."""
    errores = []
    for campo, nombre in (("nombre", "el nombre"), ("correo", "el correo de contacto"), ("ciudad", "la ciudad")):
        if not borrador[campo]:
            errores.append(f"Datos básicos: falta {nombre}.")
    if borrador["correo"] and "@" not in borrador["correo"]:
        errores.append("Datos básicos: el correo de contacto no es válido.")

    def revisar_fechas(etiqueta, inicio, fin, vigente):
        for valor, nombre in ((inicio, "inicio"), (fin, "fin")):
            if nombre == "fin" and (vigente or not valor):
                continue
            if not valor:
                errores.append(f"{etiqueta}: falta la fecha de inicio (AAAA-MM-DD).")
                continue
            try:
                datetime.strptime(valor, FORMATO_FECHA)
            except ValueError:
                errores.append(f"{etiqueta}: la fecha de {nombre} debe ir como AAAA-MM-DD.")

    for i, e in enumerate(borrador["experiencia"], start=1):
        etiqueta = f"Experiencia {i}"
        if not e["cargo"] or not e["empresa"]:
            errores.append(f"{etiqueta}: faltan el cargo o la empresa.")
        revisar_fechas(etiqueta, e["fecha_inicio"], e["fecha_fin"], e["actual"])
    for i, e in enumerate(borrador["educacion"], start=1):
        etiqueta = f"Educación {i}"
        if not e["titulo"] or not e["institucion"]:
            errores.append(f"{etiqueta}: faltan el título o la institución.")
        revisar_fechas(etiqueta, e["fecha_inicio"], e["fecha_fin"], e["en_curso"])
    return errores


def borrarPerfilParcial(correo):
    """Si el guardado falla a mitad de camino, deja el perfil vacío como estaba."""
    conexion, cursor = conectar(), None
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM Experiencia WHERE Correos_experiencia = %s", (correo,))
        cursor.execute("DELETE FROM Educacion WHERE Correos_educacion = %s", (correo,))
        cursor.execute("DELETE FROM informacion_usuarios WHERE Correos = %s", (correo,))
        conexion.commit()
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def guardarPerfilImportado(correo, borrador):
    """Guarda en el perfil lo que el usuario confirmó (decisión 7).

    Retorna (True, mensaje) o (False, mensaje).
    """
    errores = erroresBorrador(borrador)
    if errores:
        return False, "Revisa antes de guardar:\n" + "\n".join(f"- {e}" for e in errores)

    datos = {
        "nombre_completo": borrador["nombre"],
        "titular": borrador["titular"] or None,
        "contacto": {
            "correo": borrador["correo"],
            "telefono": borrador["telefono"] or None,
            "ciudad": borrador["ciudad"],
        },
        "experiencia": [dict(e, fecha_fin=e["fecha_fin"] or None) for e in borrador["experiencia"]],
        "educacion": [dict(e, fecha_fin=e["fecha_fin"] or None) for e in borrador["educacion"]],
        "habilidades": borrador["habilidades"],
        "idiomas": borrador["idiomas"],
    }
    exito, mensaje = añadirDatosExtraidos(correo, datos)
    if not exito:
        if mensaje != "Ya tienes un perfil creado":
            try:
                borrarPerfilParcial(correo)
            except Error as e:
                print(f"Fallo en las operaciones de arriba {e}")
        return False, mensaje
    n_exp, n_edu = len(datos["experiencia"]), len(datos["educacion"])
    return True, (
        f"Guardaste tu perfil con {n_exp} experiencia(s) y {n_edu} estudio(s). "
        "Puedes verlo y completarlo en «Llenar mi perfil manualmente»."
    )
