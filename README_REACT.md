# Progent en React + FastAPI

Migración de la interfaz de Streamlit a **React** con una API en **FastAPI**, según el prompt del equipo.
La lógica de `Code/` **no se reescribió**: la API solo traduce HTTP ⇄ las funciones de siempre.
**La app de Streamlit sigue intacta** y funcionando hasta que Jerónimo apruebe el retiro.

## Qué hay

```
api/                 FastAPI. Agrega Code/ al sys.path; un router por área.
  main.py            arranque, CORS, manejo de errores, modelo simulado
  nucleo.py          respuesta uniforme {ok, mensaje, datos}, sesión JWT en cookie httpOnly, descargas RFC 5987
  columnas.py        nombres de columnas para las consultas SELECT * de datosUsuario
  simulado.py        modelo de lenguaje simulado (el mismo del kit de pruebas)
  routers/           cuenta (auth + resumen), perfil, vacantes, postulaciones
  tests/             23 pruebas con pytest (+ archivos de prueba del kit)
web/                 React 18 + TypeScript + Vite, React Router, TanStack Query,
                     Tailwind CSS 4, Radix UI, React Hook Form + Zod, lucide-react
  src/estilos.css    tokens de diseño (colores, tipografía, radios): ningún color va escrito a mano
  src/componentes/   base (botón, campo, tarjeta, etapa, aviso del agente, estado vacío…), menú, carta
  src/pantallas/     login, /_estilo, perfil (5), vacantes, guardadas, recomendaciones, notificaciones, postulaciones
  e2e/e2e_react.py   prueba de punta a punta con Playwright (todas las pantallas)
cambios_logica/      arreglos en Code/ propuestos aparte (ver abajo)
```

## Cómo levantarlo

Requisitos: Python 3.11+, Node 20+, MySQL/MariaDB con la base cargada y el `.env` de siempre en la raíz.

```bash
# 1. Base de datos (si no existe)
mysql --default-character-set=utf8mb4 -u root -p < db/schema.sql

# 2. API (en una terminal)
pip install -r requirements.txt python-docx
pip install -r api/requirements.txt
cd api
uvicorn main:app --reload --port 8000

# 3. Frontend (en otra terminal)
cd web
npm install
npm run dev            # http://localhost:5173  (el /api va al puerto 8000 por el proxy de Vite)
```

En Windows con PowerShell es lo mismo; si `uvicorn` no se reconoce, usa `python -m uvicorn main:app --reload --port 8000`.

**Modelo simulado** (para probar sin gastar la clave de Anthropic):
`PROGENT_MODELO_SIMULADO=1 uvicorn main:app --port 8000` (en PowerShell: `$env:PROGENT_MODELO_SIMULADO="1"`).
El modo se elige en `/tmp/modo_modelo.txt`: `normal`, `vacio`, `basura`, `error` o `dudoso`.

Variables opcionales de la API: `PROGENT_JWT_SECRETO` (si no está, se genera una al arrancar y las sesiones se pierden al reiniciar),
`PROGENT_COOKIE_SEGURA=1` (cookie solo por HTTPS, para producción) y `PROGENT_ORIGENES` (orígenes CORS, separados por comas).

## Pruebas

```bash
cd api && pytest -q                                        # 23 pruebas de la API
# Con la API en modo simulado y el frontend corriendo:
PROGENT_URL=http://localhost:5173 python web/e2e/e2e_react.py
```

La prueba de punta a punta usa `sudo mysql` para preparar datos; cámbialo con `PROGENT_MYSQL="mysql -uroot -pTU_CLAVE"`.

Las pruebas de la API cubren la sesión (401, token falso, cerrar sesión), el **dueño de los datos** (otro usuario no ve ni
cambia mis postulaciones; el correo sale del token, no del cuerpo), la **validación de archivos** (formato, firma, tamaño de
2 y 5 MB), la **decisión 7** (extraer, recomendar y generar el CV no guardan nada hasta confirmar), la descarga con tildes
(RFC 5987) y los flujos de cada área.

## Decisiones tomadas

- **Sesión:** JWT HS256 en la cookie `progent_sesion` (httpOnly, SameSite=Lax, 8 horas). El correo siempre sale del token.
- **Respuestas:** `{ "ok", "mensaje", "datos" }` con fechas ISO 8601. Los mensajes de la lógica llegan tal cual.
  El formato de fechas (`dd/mm/aaaa a las hh:mm`, "en 3 días", "mañana") lo hace el frontend con las reglas de `entrevistas.py`.
- **Recomendaciones (#25):** `GET /api/recomendaciones/estado` devuelve la `base` (resumida con SHA-256, para que el perfil no
  viaje al navegador) y las candidatas; el frontend aplica la misma regla de `actualizar_recomendaciones`.
- **Lo que propone el agente** (borradores, sugerencias, recomendaciones, prioridades, compatibilidad, formulario) vive en el
  cliente, en la caché de TanStack Query, hasta que el usuario confirma. Se borra al cerrar sesión.
- **`GET /api/resumen`** corre `revisarAlertas` y trae el contador y los recordatorios; el menú lo pide al cargar y al cambiar de sección.
- **Diseño:** los tokens del prompt (índigo, turquesa, etapas…). Se agregaron variantes `-fuerte` de cada estado para texto
  sobre fondos suaves, porque el ámbar `#F59E0B` sobre blanco no cumple el contraste AA. La fuente Inter va empaquetada
  (`@fontsource-variable/inter`), sin depender de Google Fonts.
- **Móvil:** el menú lateral pasa a una barra inferior con rótulos cortos (Perfil, Vacantes, Sugeridas, Guardadas, Procesos,
  Avisos); el nombre accesible de cada enlace es el completo.
- La página **`/_estilo`** muestra tokens y componentes para que Jerónimo apruebe la dirección visual.

## Pendientes y notas

- **Portar las 27 suites del kit** a la app de React. Por ahora hay una suite propia (`web/e2e/e2e_react.py`) que recorre
  todas las pantallas con los textos de los criterios, más las 23 pruebas de la API.
- **«¿Olvidaste tu contraseña?»** sigue sin hacer nada, igual que en Streamlit, y **«Continuar con Google / LinkedIn»** sigue
  deshabilitado (requiere OAuth).
- **`python-docx` no está en `requirements.txt`** y la lógica lo usa (leer Word y generar el CV): hay que agregarlo.
- Antes de producción: definir `PROGENT_JWT_SECRETO`, activar `PROGENT_COOKIE_SEGURA=1` y servir `web/dist` desde el mismo origen que la API.

## Cambios propuestos a la lógica (`cambios_logica/`)

`0001-login-correo-sin-cuenta.patch`: `login.iniciarSesion` lanzaba `TypeError` cuando el correo no estaba registrado, y en
Streamlit la pantalla se caía; además buscaba el correo sin pasarlo a minúsculas, aunque el registro sí lo guarda así.
El parche devuelve `False` en ese caso y busca en minúsculas. La API ya se protege sin el parche, pero la app de Streamlit lo
necesita. Para aplicarlo: `git apply cambios_logica/0001-login-correo-sin-cuenta.patch`.
