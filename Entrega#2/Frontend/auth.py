# ---------------------------------------------------------------------------
# Usuarios de prueba (temporal — se borra cuando conectemos la base de datos)
# ---------------------------------------------------------------------------
USUARIOS_DE_PRUEBA = {
    "jjaramila1@correo.com": "Progent2026",
    "jdvivas09@correo.com": "Progent2026",
}
 
 
def verificar_login(correo, contrasena):
    if correo in USUARIOS_DE_PRUEBA:
        return USUARIOS_DE_PRUEBA[correo] == contrasena
    return False
 
 
def usuario_existe(correo):
    return correo in USUARIOS_DE_PRUEBA
 
 
def registrar_usuario(correo, contrasena):
    if usuario_existe(correo):
        return False, "Ya existe una cuenta con ese correo."
 
    # En la versión real aquí se genera el salt, se hashea la contraseña
    # y se hace el INSERT en la tabla usuarios.
    USUARIOS_DE_PRUEBA[correo] = contrasena
    return True, "Cuenta creada. Ya puedes iniciar sesión."