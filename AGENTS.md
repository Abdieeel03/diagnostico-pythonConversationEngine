# AGENTS.md — diagnostico-pythonConversationEngine

Motor de conversación Python (FastAPI + Groq + PostgreSQL). Escucha en :8000. Lee primero el `AGENTS.md` del repo padre para contexto global.

## 1. Stack

- **Python 3.12** (`python:3.12.9-slim` en Docker).
- **FastAPI 0.136.3** + **Uvicorn 0.48.0** (ASGI).
- **Pydantic v2.13.4** para schemas.
- **httpx 0.28.1** para llamadas a Prolog.
- **groq SDK 1.4.0** → modelo `llama-3.3-70b-versatile`, temperature 0.4.
- **RapidFuzz 3.14.5** para fuzzy matching en NLP.
- **SQLAlchemy 2.0.36** (async) + **asyncpg 0.30.0** + **Alembic 1.14.0** para persistencia.
- **python-dotenv** para `.env`.

## 2. Estructura

```
run.py                          → uvicorn src.main:app (auto-migración + seed al arrancar)
requirements.txt                → deps pinnadas
.env / .env.example             → PROLOG_ENGINE_URL, PORT, GROQ_API_KEY, DATABASE_URL, AUTO_MIGRATE
Dockerfile                      → python:3.12-slim, CMD python run.py
alembic.ini                     → config de Alembic
alembic/
  env.py                        → carga settings + Base.metadata
  script.py.mako                → template de migraciones
  versions/
    0001_initial.py             → esquema inicial completo + trigger
scripts/
  seed_symptoms.py              → carga catálogo desde Prolog
  test_groq.py  test_nlp.py     → scripts manuales (no pytest)
src/
  main.py                       → app FastAPI + routers
  config/settings.py            → Settings (singleton)
  routes/
    chat_routes.py              → POST /chat
    health_routes.py            → GET /health, GET /health-prolog (proxy a Prolog)
  services/
    diagnosis_service.py        → orquestador (NUEVO: usa DB en vez de RAM)
    nlp_service.py              → extracción síntomas
    prolog_service.py           → cliente HTTP Prolog
    groq_service.py             → cliente LLM
  db/
    models.py                   → modelos SQLAlchemy
    session.py                  → engine + AsyncSessionLocal + get_db
  repositories/
    chat_repository.py          → CRUD de sesiones/mensajes/síntomas/diagnósticos
  schemas/
    chat_schema.py              → ChatRequest (NUEVO: client_id, client_msg_id)
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
- Respuestas siempre vía `src/utils/response.py` (`success_response`, `error_response`).
- Diccionarios NLP: claves = átomos Prolog (`dolor_cabeza`); valores = listas de keywords/sinónimos en español natural.
- Repositorios: una clase por agregado, recibe `AsyncSession` por constructor.

## 4. Variables de entorno

| Variable | Default | Uso |
|---|---|---|
| `PROLOG_ENGINE_URL` | `http://localhost:5000` | URL del motor Prolog |
| `PORT` | `8000` | Puerto Uvicorn |
| `GROQ_API_KEY` | `''` | API key de Groq (obligatoria en prod) |
| `DATABASE_URL` | `postgresql+asyncpg://diagnostico:diagnostico_secret@localhost:5432/diagnostico_db` | Conexión a Postgres (asyncpg) |
| `AUTO_MIGRATE` | `true` | Si `true`, `run.py` corre `alembic upgrade head` antes de uvicorn |
| `RELOAD` | `false` | Uvicorn autoreload (sólo dev) |
| `PROLOG_FACTS_PATH` | — | Ruta absoluta a `sintomas.pl` (auto-detectada en Docker) |

## 5. Flujo de `POST /chat`

`diagnosis_service.process_message(message, client_id, client_msg_id)`:

1. **Sesión**: `repo.get_or_create_session(client_id)` busca la última sesión con ese `client_id` o crea una nueva.
2. **Idempotencia**: si llega `client_msg_id` y ya existe un mensaje con ese id en la sesión, devuelve `duplicate: true` sin reprocesar.
3. **Catálogo**: `repo.get_known_symptom_keys()` carga los síntomas válidos (set de `sintoma_catalogo`).
4. **NLP**: `nlp_service.extract_symptoms(message)` → filtrado por catálogo.
5. **Acumulación**: `repo.get_session_symptoms(session_id)` carga los síntomas previos de la sesión y los une con los nuevos (deduplicado).
6. **Persistencia user**: `repo.add_user_message(...)` guarda el mensaje del usuario y sus síntomas detectados (FK a catálogo).
7. **Sin síntomas** → respuesta fallback, `repo.add_assistant_message(...)`, commit, return.
8. **Prolog**: `prolog_service.get_diagnostico(accumulated_symptoms)` → orden por score desc.
9. **Filtrado**: 1 síntoma → top 3; 2 → top 5; ≥3 → `coincidencias ≥ 2` (top 5).
10. **most_probable**: sólo si hay 2+ síntomas.
11. **context_note**: guía al LLM según la cantidad de síntomas.
12. **Groq**: `groq_service.generate_response(...)` con historial cargado de la DB. Si falla, fallback genérico.
13. **Persistencia assistant**: `repo.add_assistant_message(...)`.
14. **Persistencia diagnósticos**: `repo.add_diagnostics(...)` (uno por enfermedad devuelta por Prolog, FK a sesión + mensaje).
15. **Commit** + respuesta con `session_id, response, symptoms, diagnosticos, most_probable`.

## 6. Persistencia (PostgreSQL)

Esquema en `alembic/versions/0001_initial.py`. Tablas:

| Tabla | Para qué |
|---|---|
| `sintoma_catalogo` | Lista de átomos Prolog válidos. Seed automático al arrancar. |
| `chat_session` | Una fila por sesión. `client_id` = el `session_id` del frontend. |
| `chat_message` | Cada turno (user/assistant). `client_msg_id` opcional para idempotencia. |
| `chat_symptom` | N fila por mensaje con síntoma detectado. FK a catálogo. |
| `chat_diagnostic` | N fila por enfermedad devuelta por Prolog en una llamada. FK a sesión y opcional a mensaje. |

El ENUM `remitente_tipo` se crea con `('user', 'assistant')`. El trigger `trg_set_updated_at` mantiene fresco `chat_session.updated_at`.

Auto-migración: al arrancar `run.py`, si `AUTO_MIGRATE=true`, corre `alembic upgrade head` y luego, si `sintoma_catalogo` está vacío, ejecuta `scripts/seed_symptoms.py` que parsea los átomos desde `sintomas.pl`.

## 7. Prompt del LLM

En `src/services/groq_service.py`. Instrucciones clave (ya estaban, sin cambios):

- Responder en español, tono cercano y natural.
- **No mencionar** motores expertos, algoritmos, scores, porcentajes, coincidencias.
- No explicar cómo se obtuvo el resultado.
- No inventar enfermedades ni síntomas fuera del listado.
- No decir que es diagnóstico definitivo.
- Máximo 2 párrafos; si hay pocos síntomas, sólo 1.
- No repetir varias veces la recomendación de consultar profesional.
- Si no hay enfermedad principal, no mencionar enfermedades específicas; pedir más síntomas.

> Cualquier cambio en el prompt debe mantener o reforzar el disclaimer médico.

## 8. Endpoints

| Método | Ruta | Body | Descripción |
|---|---|---|---|
| GET | `/` | — | Health root del servicio Python |
| GET | `/health` | — | Health propio del servicio Python |
| GET | `/health-prolog` | — | Proxy a `GET /health` de Prolog |
| POST | `/chat` | `{message, client_id, client_msg_id?}` | Orquestación completa (persiste en DB) |

Respuesta de `/chat`:
```json
{
  "success": true,
  "message": "Respuesta generada correctamente",
  "data": {
    "session_id": 42,
    "response": "...",
    "symptoms": ["fiebre", "tos"],
    "diagnosticos": [{"enfermedad": "gripe", "score": 0.85, "coincidencias": 5}],
    "most_probable": {"enfermedad": "gripe", "score": 0.85, "coincidencias": 5}
  }
}
```

## 9. Gotchas (no reintroducir)

### Resueltos (no reintroducir)

1. ~~**`prolog_service.get_diagnostico` sin `success` en error**~~ — ya devuelve `{success: false, message, data: null}` en `RequestError` y `HTTPStatusError`.
2. ~~**`run.py` usa `reload=True` en prod**~~ — `reload` es condicional por env var `RELOAD`; docker-compose setea `RELOAD=false`.
3. ~~**`groq_service` síncrono sin timeout/reintentos**~~ — ya usa `AsyncGroq` con timeout de 30s, reintentos con backoff exponencial (`MAX_RETRIES=2`).
4. ~~**`health_routes.py` sin `success_response`**~~ — `GET /health-prolog` ya reenvuelve con envelope propio.
5. ~~**Sin `/health` propio**~~ — ya existe `GET /health` en `health_routes.py`.
6. ~~**Memoria de chat en RAM (`_SessionStore`)**~~ — reemplazado por Postgres + repositorio. El `_SessionStore` fue eliminado de `diagnosis_service.py`.
7. ~~**SSL no propagado al runtime asyncpg**~~ — `db/session.py` ahora adapta la URL: extrae `sslmode` del query string y lo pasa como `ssl=True` (o `False`) en `connect_args` para `asyncpg.connect()`, que es el formato que asyncpg espera. El seed (que usa `psycopg2` directamente) sigue pasando `sslmode` como kwarg, que también es válido.

### Vigentes

1. **`_extract_symptoms_with_confidence`** en `nlp_service.py` está definido pero **sin usar** (código muerto).
2. **Sin tests pytest** — sólo `scripts/test_*.py` sueltos. Configurar `pytest` + `pytest-asyncio`.
3. **Sin type-checker** (mypy no instalado) ni lint (ruff no instalado).
4. **Groq service sin fallback para errores recuperables** — si Groq falla, ahora devolvemos un mensaje genérico en vez de propagar 500, pero el mensaje es estático y podría ser más útil.
5. **Migraciones Alembic autogenerate no probadas** — la migración inicial está escrita a mano para incluir el trigger; las próximas deberían autogenerarse con `alembic revision --autogenerate -m "..."` y revisarse.

## 10. Cómo extender

- **Añadir sinónimos de síntoma**: edita el archivo en `src/data/symptoms/<area>.py` correspondiente; la clave debe coincidir exactamente con un átomo Prolog. NO añadir claves nuevas sin que existan en `sintomas.pl` (Prolog) — al guardar mensaje fallará la FK a `sintoma_catalogo`.
- **Añadir área nueva de síntomas**: crea `src/data/symptoms/<area>.py` con un dict `FOO_SYMPTOMS = {...}` y agrégarlo en `symptoms_dictionary.py`.
- **Cambiar el prompt**: `src/services/groq_service.py`. Mantener el disclaimer.
- **Nuevo endpoint**: ruta en `src/routes/<name>_routes.py`, router incluido en `src/main.py`. Respuesta vía `utils/response.py`.
- **Nueva migración**: `alembic revision --autogenerate -m "descripcion"`, revisar el archivo generado, `alembic upgrade head`.
- **Nueva columna en tabla existente**: misma mecánica; el trigger `trg_set_updated_at` no necesita cambios (sólo toca `chat_session`).
- **Mockear Prolog/Groq en tests**: usar `monkeypatch` sobre `prolog_service.get_diagnostico` y `groq_service.generate_response`.

## 11. Verificación

| Comando | Uso |
|---|---|
| `python run.py` | arranque local (auto-migra + seed + uvicorn :8000) |
| `curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"tengo fiebre y tos","client_id":"test-1"}' \| jq` | smoke test |
| `python scripts/test_nlp.py` | smoke test NLP manual |
| `python scripts/test_groq.py` | smoke test Groq manual (requiere GROQ_API_KEY) |
| `python scripts/seed_symptoms.py` | repoblar catálogo (idempotente) |
| `alembic current` | ver la migración aplicada |
| `alembic upgrade head` | aplicar migraciones pendientes |
| `alembic downgrade -1` | revertir la última migración |

**Pendientes** (no existen aún — preguntar al usuario antes de invocar):
- pytest: `pytest tests/`
- typecheck: `mypy src`
- lint: `ruff check src`

## 12. Docker

```dockerfile
FROM python:3.12.9-slim
WORKDIR /app
COPY diagnostico-pythonConversationEngine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY diagnostico-pythonConversationEngine/src/ ./src/
COPY diagnostico-pythonConversationEngine/scripts/ ./scripts/
COPY diagnostico-pythonConversationEngine/alembic/ ./alembic/
COPY diagnostico-pythonConversationEngine/alembic.ini ./alembic.ini
COPY diagnostico-pythonConversationEngine/run.py ./run.py
COPY diagnostico-prologEngine/src/knowledge/facts/sintomas.pl /app/diagnostico-prologEngine/src/knowledge/facts/sintomas.pl
ENV PROLOG_FACTS_PATH=/app/diagnostico-prologEngine/src/knowledge/facts/sintomas.pl
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["python", "run.py"]
```

El build context es el padre (`./`), no el submódulo, para poder copiar el `sintomas.pl` del submódulo Prolog dentro de la imagen y que el seed funcione.

Mejora pendiente: pinnear imagen por digest SHA para builds 100% reproducibles.

## 13. Reglas para agentes (específicas)

- Mantén el contrato `{success, message, data}` en cada endpoint.
- Nunca inventes claves de síntomas que no existan en Prolog (`diagnostico-prologEngine/src/knowledge/facts/sintomas.pl`) — la FK a `sintoma_catalogo` fallará en runtime.
- No hardcodees URLs de Prolog/Groq/Postgres: siempre desde `src/config/settings.py`.
- No agregues dependencias nuevas sin verificar `requirements.txt` y confirmar con el usuario.
- Refuerza el disclaimer: cualquier prompt nuevo o respuesta visible debe recordar que es orientación educativa.
- Si modificas `process_message`, ejecuta `python scripts/test_nlp.py` como smoke test mínimo.
- Cualquier cambio de esquema debe ir a una nueva migración Alembic (`alembic revision --autogenerate -m "..."`), NUNCA editar `0001_initial.py` después de que se haya aplicado.
