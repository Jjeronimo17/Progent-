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

## Cómo ejecutarlo

> [!NOTE]
> El código de cada sprint vive en su propia carpeta. Lo siguiente corresponde a la
> entrega actual.

**1. Ubícate en la carpeta de la entrega**

```bash
cd Entrega#2
```

**2. Crea el entorno virtual e instala las dependencias**

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

**3. Configura la clave de API**

```bash
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```

Abre el `.env` y pega tu clave de Anthropic.

**4. Ejecuta la aplicación**

```bash
streamlit run main.py
```

> [!WARNING]
> La clave de API va en `.env`, que está listado en `.gitignore`. **Nunca** la subas
> al repositorio. Si se filtra, revócala de inmediato desde la consola de Anthropic.

---

## Stack

| Componente | Tecnología |
|---|---|
| Orquestación de agentes | LangGraph |
| Modelo de lenguaje | API de Anthropic |
| Interfaz | Streamlit |
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
