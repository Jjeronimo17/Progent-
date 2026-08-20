# Progent — Prueba de concepto

Importar una hoja de vida en PDF y estructurarla con un agente en LangGraph.

- **Entrada:** el usuario sube su hoja de vida en PDF.
- **Proceso:** un grafo de tres nodos extrae el texto, lo envia al modelo pidiendo
  JSON estructurado y valida el resultado.
- **Salida:** los datos del perfil en pantalla, editables y confirmables por el usuario.

## Montar el ambiente

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # y pegar la clave real dentro
streamlit run app.py
```

Probar solo el grafo, sin interfaz:

```bash
python graph.py ruta/al/cv.pdf
```py

## Estructura

| Archivo | Que hace |
|---|---|
| `graph.py` | El grafo de LangGraph: leer_pdf -> extraer -> validar |
| `prompts.py` | El prompt del agente y el esquema de salida |
| `app.py` | Interfaz de subida, revision y confirmacion |

## Nota

La clave de API va en `.env`, que esta en `.gitignore`. Nunca subirla al repositorio.
