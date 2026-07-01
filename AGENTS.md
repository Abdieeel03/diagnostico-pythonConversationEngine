# AGENTS.md — diagnostico-pythonConversationEngine

Motor de conversación Python (FastAPI + Groq). Escucha en :8000. Lee primero el `AGENTS.md` del repo padre para contexto global.

## 1. Stack

- **Python 3.12** (`python:3.12.9-slim` en Docker).
- **FastAPI 0.136.3** + **Uvicorn 0.48.0** (WSGI/ASGI).
- **Pydantic v2.13.4** para schemas.
- **httpx 0.28.1** para llamadas a Prolog.
- **groq SDK 1.4.0** → modelo `llama-3.3-70b-versatile`, temperature 0.4.
- **RapidFuzz 3.14.5** para fuzzy matching en NLP.
- **python-dotenv** para `.env`.

## 2. Estructura

```
run.py                          → uvicorn src.main:app
requirements.txt                → deps pinnadas
.env / .env.example             → PROLOG_ENGINE_URL, PORT, GROQ_API_KEY
Dockerfile                      → python:3.12-slim, CMD python run.py
scripts/
  test_groq.py  test_nlp.py     → scripts manuales (no pytest)
src/
  main.py                       → app FastAPI + routers
  config/settings.py            → Settings (singleton)
  routes/
    chat_routes.py              → POST /chat
    health_routes.py            → GET /health, GET /health-prolog (proxy a Prolog)
  services/
    diagnosis_service.py        → orquestador
    nlp_service.py              → extracción síntomas
    prolog_service.py           → cliente HTTP Prolog
    groq_service.py             → cliente LLM
  schemas/
    chat_schema.py              → ChatRequest
  data/
    symptoms_dictionary.py      → agrega todos los subdiccionarios
    symptoms/
      digestive.py general.py metabolic.py neurological.py
      ocular_ear.py pain.py respiratory.py skin.py urinary.py
  utils/
    response.py                 → success_response / error_response
```

## 3. Convenciones Python

- Indentación: **2 espacios**.
- `src/` con subpaquetes; imports absolutos desde `src.` (ej. `from src.services.diagnosis_service import diagnosis_service`).
- Servicios como **clases**, instanciadas una sola vez al final del archivo (`foo_service = FooService()`). Inyección por importación directa (sin DI framework).
- Settings vía `src/config/settings.py` (env vars con `python-dotenv`).
- Schemas Pydantic v2 en `src/schemas/`.
- Respuestas siempre vía `src/utils/response.py` (`success_response`, `error_response`) — nunca `JSONResponse` directo desde el route.
- Diccionarios NLP: claves = átomos Prolog (`dolor_cabeza`); valores = listas de keywords/sinónimos en español natural.

## 4. Variables de entorno

| Variable | Default | Uso |
|---|---|---|
| `PROLOG_ENGINE_URL` | `http://localhost:5000` | URL del motor Prolog |
| `PORT` | `8000` | Puerto Uvicorn |
| `GROQ_API_KEY` | `''` | API key de Groq (obligatoria en prod) |

## 5. Flujo de `POST /chat`

`diagnosis_service.process_message(message)`:

1. **NLP** (`nlp_service.extract_symptoms`): normaliza texto (NFD + lowercase + quita diacríticos), itera el diccionario, matchea keywords con regex `\b` exacto; si keyword ≥6 chars y multi-palabra, fuzzy con `fuzz.ratio ≥ 90` en ventanas deslizantes.
2. Sin síntomas → `{response: pidiendo más detalle, symptoms: [], diagnosticos: [], most_probable: null}`.
3. **Prolog** (`prolog_service.get_diagnostico`) → POST `/diagnostico`.
4. Ordena por `score` desc.
5. Filtra: 1 síntoma → top 3; 2 síntomas → top 5; ≥3 → `coincidencias ≥ 2` (top 5).
6. `most_probable` = `diagnosticos[0]` sólo si hay 2+ síntomas.
7. `context_note` guía al LLM según cantidad de síntomas.
8. **Groq** (`groq_service.generate_response`) → LLM con prompt ya montado.
9. Devuelve `{response, symptoms, diagnosticos, most_probable}` envuelto en `{success, message, data}`.

## 6. Prompt del LLM

En `src/services/groq_service.py`. Instrucciones clave del system-prompt (hoy embebidas en user):

- Responder en español, tono cercano y natural.
- **No mencionar** motores expertos, algoritmos, scores, porcentajes, coincidencias.
- No explicar cómo se obtuvo el resultado.
- No inventar enfermedades ni síntomas fuera del listado.
- No decir que es diagnóstico definitivo.
- Máximo 2 párrafos; si hay pocos síntomas, sólo 1.
- No repetir varias veces la recomendación de consultar profesional (una vez al final).
- Si no hay enfermedad principal, no mencionar enfermedades específicas; pedir más síntomas.

> Cualquier cambio en el prompt debe mantener o reforzar el disclaimer médico.

## 7. Endpoints

| Método | Ruta | Body | Descripción |
|---|---|---|---|
| GET | `/` | — | Health root del servicio Python |
| GET | `/health` | — | Health propio del servicio Python |
| GET | `/health-prolog` | — | Proxy a `GET /health` de Prolog (reenvuelve con envelope propio) |
| POST | `/chat` | `{"message": "..."}` | Orquestación completa |

## 8. Gotchas (no reintroducir)

### Resueltos (no reintroducir)

1. ~~**`prolog_service.get_diagnostico` sin `success` en error**~~ — ya devuelve `{success: false, message, data: null}` en `RequestError` y `HTTPStatusError`.
2. ~~**`run.py` usa `reload=True` en prod**~~ — `reload` es condicional por env var `RELOAD` (`true`/`1`/`yes`); docker-compose setea `RELOAD=false`.
3. ~~**`groq_service` síncrono sin timeout/reintentos**~~ — ya usa `AsyncGroq` con timeout de 30s, reintentos con backoff exponencial (`MAX_RETRIES=2`).
4. ~~**`health_routes.py` sin `success_response`**~~ — `GET /health-prolog` ya reenvuelve con envelope propio vía `success_response`/`error_response`.
5. ~~**Sin `/health` propio**~~ — ya existe `GET /health` en `health_routes.py`.

### Vigentes

1. **`_extract_symptoms_with_confidence`** en `nlp_service.py` está definido pero **sin usar** (código muerto).
2. **Sin tests pytest** — sólo `scripts/test_*.py` sueltos. Configurar `pytest` + `pytest-asyncio`.
3. **Sin type-checker** (mypy no instalado) ni lint (ruff no instalado).
4. **Groq service sin fallback graceful** — si Groq falla tras reintentos, `generate_response` lanza excepción que propaga a 500; el usuario ve error genérico. Considerar fallback con mensaje estático.

## 9. Cómo extender

- **Añadir sinónimos de síntoma**: edita el archivo en `src/data/symptoms/<area>.py` correspondiente; la clave debe coincidir exactamente con un átomo Prolog. NO añadir claves nuevas sin que existan en `sintomas.pl` (Prolog) o el síntoma no hará match.
- **Añadir área nueva de síntomas**: crea `src/data/symptoms/<area>.py` con un dict `FOO_SYMPTOMS = {...}` y agrégarlo en `symptoms_dictionary.py`.
- **Cambiar el prompt**: `src/services/groq_service.py`. Mantener el disclaimer.
- **Nuevo endpoint**: ruta en `src/routes/<name>_routes.py`, router incluido en `src/main.py`. Respuesta vía `utils/response.py`.
- **Mockear Prolog/Groq en tests**: usar `monkeypatch` sobre `prolog_service.get_diagnostico` y `groq_service.generate_response`.

## 10. Verificación

| Comando | Uso |
|---|---|
| `python run.py` | arranque local (uvicorn :8000; `reload` depende de env var `RELOAD`) |
| `curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"tengo fiebre y tos"}' \| jq` | smoke test |
| `python scripts/test_nlp.py` | smoke test NLP manual |
| `python scripts/test_groq.py` | smoke test Groq manual (requiere GROQ_API_KEY) |

**Pendientes** (no existen aún — preguntar al usuario antes de invocar):
- pytest: `pytest tests/`
- typecheck: `mypy src`
- lint: `ruff check src`

## 11. Docker

```dockerfile
FROM python:3.12.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["python", "run.py"]
```

Mejora pendiente: pinnear imagen por digest SHA para builds 100% reproducibles.

## 12. Reglas para agentes (específicas)

- Mantén el contrato `{success, message, data}` en cada endpoint.
- Nunca inventes claves de síntomas que no existan en Prolog (`diagnostico-prologEngine/src/knowledge/facts/sintomas.pl`) o se romperá el match en runtime.
- No hardcodees URLs de Prolog/Groq: siempre desde `src/config/settings.py`.
- No agregues dependencias nuevas sin verificar `requirements.txt` y confirmar con el usuario.
- Refuerza el disclaimer: cualquier prompt nuevo o respuesta visible debe recordar que es orientación educativa.
- Si modificas `process_message`, ejecuta `python scripts/test_nlp.py` como smoke test mínimo.