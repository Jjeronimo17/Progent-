<div align="center">

# Progent

**Profile Manager con arquitectura agéntica**

*Gestiona tu perfil. Encuentra oportunidades. Un agente que trabaja para ti.*

![Estado](https://img.shields.io/badge/estado-en%20desarrollo-blue)
![Sprint](https://img.shields.io/badge/sprint-2-orange)
![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?logo=langchain&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Uso](https://img.shields.io/badge/uso-académico-lightgrey)

</div>

---

## Qué es Progent

Progent es un **gestor de perfil para personas en búsqueda de empleo**. En lugar de
obligar al usuario a llenar los mismos formularios una y otra vez, un conjunto de
agentes interpreta su hoja de vida, construye su perfil, le recomienda vacantes
acordes y prepara el contenido de cada postulación.

El proyecto se desarrolla para la empresa **Magneto** dentro del curso de Ingeniería
de Software de la Universidad EAFIT, bajo metodología Scrum.

### El problema

El modelo tradicional de postulación tiene tres fricciones que Progent ataca:

| Fricción | Cómo la aborda Progent |
|---|---|
| Llenar formularios repetitivos en cada portal | Un agente genera las respuestas con la información ya guardada en el perfil |
| Perfiles incompletos o desactualizados | Un agente interpreta el CV y el usuario solo revisa y confirma |
| No saber en qué va cada proceso | Un panel centraliza el estado de todas las postulaciones |

### Qué NO es Progent

> [!IMPORTANT]
> Estas fronteras son decisiones de alcance tomadas durante el inception y sostenidas
> a lo largo del proyecto.

- **No es un portal de empleo.** Progent no publica vacantes; las consulta de fuentes externas.
- **No envía postulaciones.** Prepara el contenido dentro de Progent; el usuario lo lleva al portal de la vacante.
- **No accede al correo del usuario.** El seguimiento del proceso lo alimenta el propio usuario.
- **No garantiza empleo ni actúa como reclutador.**

---

## Cómo funciona

```
                          ┌─────────────────┐
     Usuario  ──────────► │                 │ ◄────────  Proveedor LLM
                          │     PROGENT     │ ◄────────  Portales de empleo
     Operador ──────────► │                 │ ─────────► LangSmith
                          └─────────────────┘ ─────────► Servicio de correo
```

El corazón del sistema es un **grafo de estado en LangGraph**. Cada capacidad del
producto es un flujo de nodos donde el agente propone y **el usuario confirma** —
ese control humano es una decisión de diseño central, no un detalle.

> [!NOTE]
> **Principio rector:** el agente hace el trabajo pesado; el usuario aporta la
> información y toma las decisiones.

---

## Estado actual

| Sprint | Estado |
|---|---|
| **Sprint 1** | ✅ Completado |
| **Sprint 2** | 🔨 En desarrollo |

**Entregado en el Sprint 1:** inception ágil completo (lista SÍ / NO / NO RESUELTO,
vecindario, necesidades de equipo), diagrama de contexto C4 nivel 1, diagrama de flujo
del usuario, story map con 29 historias en tres releases, backlog en GitHub Projects
con criterios de aceptación, documento de visioning y una prueba de concepto funcional.

**Prueba de concepto:** subir un CV en PDF → un agente extrae los datos estructurados →
el usuario revisa, corrige y confirma. El agente reporta los campos sobre los que no
quedó seguro, para que la revisión del usuario sea dirigida y no a ciegas.

---

## Roadmap por releases

<details>
<summary><b>Release 1 — Walking skeleton + agentes base</b></summary>

<br>

Perfil básico, importación del CV con extracción por agente, generación del CV
estructurado, listado y búsqueda de vacantes, recomendación básica y registro de
postulaciones.

</details>

<details>
<summary><b>Release 2 — Lo que R1 dejó pendiente</b></summary>

<br>

Filtros avanzados, vacantes guardadas, alertas de nuevas ofertas, carta de
presentación, interpretación del formulario de la vacante y panel de seguimiento
por etapas.

</details>

<details>
<summary><b>Release 3 — Agentes: versión completa</b></summary>

<br>

Asistente de mejora del CV según las vacantes de interés, recomendación proactiva,
compatibilidad perfil–vacante y priorización inteligente de procesos.

</details>

---

## Estructura del repositorio

```
Progent-/
├── src/                ← código de la aplicación (backend y frontend)
├── db/                 ← schema.sql y modelo EER (.mwb)
├── docs/               ← entregables, diagramas y documentación
├── .env.example        ← plantilla de variables de entorno
├── requirements.txt
└── README.md
```

> [!NOTE]
> Las entregas de cada sprint no viven en carpetas separadas: se marcan con **tags**
> de git (`entrega-1`, `entrega-2`, …) y se publican en la sección **Releases** del
> repositorio. Para ver el código exactamente como se entregó, abre el release
> correspondiente.

---

## Cómo ejecutarlo

**1. Clona el repositorio y crea el entorno virtual**

```bash
git clone https://github.com/Jjeronimo17/Progent-.git
cd Progent-

python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

**2. Instala MySQL Server 8.0** y crea la base de datos ejecutando el script del esquema,
ya sea desde MySQL Workbench o desde la terminal:

```bash
mysql -u root -p < db/schema.sql
```

**3. Configura las variables de entorno**

```bash
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```

Abre el `.env` y completa los valores: tu clave de Anthropic y los datos de
conexión a **tu** MySQL local (cada integrante usa su propia contraseña).

**4. Ejecuta la aplicación** desde la raíz del repositorio

```bash
streamlit run src/main.py
```

> [!WARNING]
> El `.env` está listado en `.gitignore`. **Nunca** subas claves ni contraseñas al
> repositorio: el repo es público. Si alguna se filtra, cámbiala de inmediato
> (borrarla en un commit posterior no basta, queda en el historial).

---

## Flujo de trabajo del equipo

> [!IMPORTANT]
> La rama `main` está **protegida**: no se puede hacer push directo a ella. Todo
> cambio — código, base de datos o documentación — entra por **pull request** con
> al menos **una aprobación** de otro integrante. Así `main` siempre funciona.

### Paso a paso para cada cambio

**1. Parte de `main` actualizado**

```bash
git switch main
git pull
```

**2. Crea una rama para tu cambio**

```bash
git switch -c feature/editar-perfil
```

| Prefijo | Para qué |
|---|---|
| `feature/` | Funcionalidad nueva |
| `fix/` | Corrección de un error |
| `docs/` | Cambios en documentación |

Una rama por historia o arreglo. Ramas pequeñas se revisan rápido y generan menos conflictos.

**3. Trabaja y haz commits en tu rama**

```bash
git add -A
git commit -m "Agrega la edición de datos de contacto"
```

Corre `git status` antes de cada commit y verifica que **no** aparezcan `.env`,
`venv/` ni `__pycache__/`.

**4. Sube la rama**

```bash
git push -u origin feature/editar-perfil   # la primera vez
git push                                    # las siguientes
```

**5. Abre la pull request** en GitHub con el botón **Compare & pull request**.
Explica qué cambia y por qué. Si resuelve una historia del backlog, escribe
`Closes #<número>` en la descripción: al fusionarla, el issue se cierra solo.

**6. Pide revisión** asignando a un compañero en **Reviewers**.

**7. Fusiona cuando tengas la aprobación** con **Squash and merge** y luego
**Delete branch**.

**8. Limpia en tu equipo**

```bash
git switch main
git pull
git branch -d feature/editar-perfil
```

### Si `main` avanzó mientras trabajabas

Trae los cambios a tu rama antes de abrir o actualizar la pull request:

```bash
git pull origin main
```

Si git reporta un conflicto, resuélvelo en los archivos marcados, haz commit y sigue.
Hacerlo seguido evita conflictos grandes.

### Al revisar la pull request de alguien

- Lee los cambios en la pestaña **Files changed**.
- Si el cambio toca el login, la base de datos o algo compartido, **baja la rama y corre la app**:
  `git fetch` y luego `git switch <nombre-de-la-rama>`.
- Verifica que no se suban credenciales ni archivos generados.
- **Approve** si todo está bien, o **Request changes** explicando qué ajustar.

### Cambios en la base de datos

Cualquier cambio de estructura (tablas, columnas, procedimientos, restricciones) debe
quedar reflejado en `db/schema.sql` **en la misma pull request** que el código que
lo usa. Si el esquema del repositorio no coincide con el código, los demás no podrán
levantar el proyecto.

> [!NOTE]
> El coordinador técnico conserva un permiso de excepción sobre `main` para
> emergencias. No es el camino normal: sus cambios también van por pull request.

---

## Stack

| Componente | Tecnología |
|---|---|
| Orquestación de agentes | LangGraph |
| Modelo de lenguaje | API de Anthropic |
| Interfaz | Streamlit |
| Base de datos | MySQL 8.0 |
| Lectura de PDF | pypdf |
| Trazabilidad | LangSmith |
| Gestión del backlog | GitHub Projects |

### Decisiones de arquitectura

| Decisión | Razón |
|---|---|
| Autenticación propia | Control total sobre las credenciales y aprendizaje del equipo |
| Base de datos de diseño propio | El modelado relacional es parte del objetivo formativo |
| Importación de LinkedIn por archivo exportado | La API de perfiles está restringida a socios; el archivo del usuario no depende de aprobaciones |
| Trazas con datos personales enmascarados | Los prompts se construyen con atributos profesionales normalizados; los identificadores directos no entran al grafo |

---

## Equipo

| Integrante | Rol |
|---|---|
| Jerónimo Jaramillo Agudelo | Full stack · coordinación técnica |
| Simón Banda | Backend |
| Miguel Ángel Jiménez | Backend |
| Juan Daniel Vivas | Frontend |

**Product Owners:** Juan Camilo Herrera · Luis Miguel Marín
**Scrum Master:** Elizabeth Suescún

---

<div align="center">
<sub>Universidad EAFIT · Departamento de Informática y Sistemas · Ingeniería de Software</sub>
</div>
