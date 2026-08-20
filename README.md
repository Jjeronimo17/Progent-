# Progent

**Profile Manager con arquitectura agéntica basada en LangGraph.**

Progent apoya a personas en búsqueda de empleo: interpreta su hoja de vida para armar
el perfil, recomienda vacantes según ese perfil, prepara el contenido de las
postulaciones y hace seguimiento de cada proceso.

Progent no envía las postulaciones al portal de la vacante. Prepara el contenido y el
usuario lo lleva.

Proyecto del curso de Ingeniería de Software — Universidad EAFIT.

---

## Documentación de la entrega

Diagramas, story map, inception ágil y video de sustentación:

**Video: (https://drive.google.com/file/d/1iJCqoskFx4mAmWSSDqj5FDc8BpaWaPzp/view?usp=sharing)**

El backlog del producto está en la pestaña **Projects** de este repositorio.

---

## Prueba de concepto

Esta primera entrega implementa una sola funcionalidad, de punta a punta, para validar
el ambiente y la arquitectura agéntica:

| | |
|---|---|
| **Entrada** | El usuario sube su hoja de vida en PDF |
| **Proceso** | Un grafo de LangGraph extrae el texto, lo envía al modelo pidiendo datos estructurados y valida el resultado |
| **Salida** | Los datos del perfil en pantalla, editables y confirmables por el usuario |

El agente reporta de qué campos no quedó seguro, para que el usuario revise esos
primero. Esa confirmación humana es una decisión de diseño central del producto.

---

## Cómo ejecutarlo

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # pegar la clave real dentro
streamlit run app.py
```

Probar solo el grafo, sin interfaz:

```bash
python graph.py cv_prueba.pdf
```

---

## Estructura

| Archivo | Qué hace |
|---|---|
| `graph.py` | El grafo de LangGraph: `leer_pdf` → `extraer` → `validar` |
| `prompts.py` | El prompt del agente y el esquema de salida |
| `app.py` | Interfaz de carga, revisión y confirmación |
| `cv_prueba.pdf` | Hoja de vida ficticia para pruebas |

---

## Stack

Python · LangGraph · API de Anthropic · Streamlit · pypdf

---

## Configuración

La clave de API va en `.env`, que está en `.gitignore` y **nunca** se sube al
repositorio. `.env.example` documenta las variables necesarias.

```
ANTHROPIC_API_KEY=
MODELO=
```

---

## Equipo

| | |
|---|---|
| Jerónimo Jaramillo Agudelo | Full stack y coordinación técnica |
| Simón Banda | Backend |
| Miguel Ángel Jiménez | Backend |
| Juan Daniel Vivas | Frontend |

Product Owners: Juan Camilo Herrera, Luis Miguel Marín
Scrum Master: Elizabeth Suescún
