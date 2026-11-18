"""Importar el perfil desde LinkedIn (historia #4).

Se usa el PDF que LinkedIn genera con «Más → Guardar en PDF» en el perfil, no el .zip
de datos ni la API (decisión del equipo). La extracción la hace el agente de graph.py
con el prompt SYSTEM_EXTRACCION_LINKEDIN.
"""

from importarPerfil import extraerPerfil


def extraerPerfilLinkedin(correo, nombre_archivo, datos):
    """Lee el PDF del perfil de LinkedIn y devuelve el borrador para revisarlo.

    Retorna lo mismo que importarPerfil.extraerPerfil.
    """
    return extraerPerfil(correo, nombre_archivo, datos, "linkedin")
