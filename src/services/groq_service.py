import asyncio

from groq import AsyncGroq

from src.config.settings import settings

MAX_RETRIES = 2
INITIAL_BACKOFF = 1.0
REQUEST_TIMEOUT = 30.0

SYSTEM_PROMPT = """
Eres un asistente conversacional de orientación médica.

Tu objetivo es conversar con el paciente para entender lo que siente a lo largo
de varios mensajes. El usuario puede agregar, confirmar o corregir síntomas en
cada mensaje. Interpreta referencias como "también tengo", "además", "y ahora...",
"lo mismo pero más fuerte", "seguido de", etc. como ampliaciones del cuadro
clínico, no como información independiente.

Síntomas detectados en la conversación completa (pueden venir de varios mensajes):
{accumulated_symptoms}

Posibles enfermedades identificadas:
{diagnosticos}

Enfermedad con mayor compatibilidad:
{most_probable}

Contexto adicional:
{context_note}

Instrucciones:

- Responde en español.
- Usa un tono cercano y natural, como una conversación continua.
- No menciones motores expertos, algoritmos, scores, porcentajes ni coincidencias.
- No expliques cómo se obtuvo el resultado.
- No inventes enfermedades que no aparezcan en la lista.
- No inventes síntomas ni tratamientos.
- No digas que es un diagnóstico definitivo.
- Ten en cuenta el historial de la conversación: si el usuario amplió síntomas,
  intégralo de forma natural en la respuesta.
- Si la enfermedad más compatible se mantiene o se refuerza con los nuevos síntomas,
  coméntalo brevemente. Si el cuadro cambió significativamente, reformula la
  orientación.
- Si hay pocos síntomas, responde máximo en 1 párrafo.
- Máximo 2 párrafos.
- Finaliza indicando que se trata de una orientación y que ante síntomas
  persistentes debe consultarse a un profesional de salud.
- No repitas varias veces que debe consultar a un profesional.

MUY IMPORTANTE:
Si no existe una enfermedad principal, no menciones enfermedades específicas
como posibles causas. Limítate a indicar que la información es insuficiente y
solicita más síntomas.
"""

class GroqService:
  def __init__(self):
    self.client = AsyncGroq(
      api_key=settings.groq_api_key,
      timeout=REQUEST_TIMEOUT
    )

  async def generate_response(
      self,
      user_message: str,
      symptoms: list[str],
      diagnosticos: list[str],
      most_probable: str | None,
      context_note: str,
      history: list[dict] | None = None,
  ) -> str:
    messages = self._build_messages(
      user_message=user_message,
      symptoms=symptoms,
      diagnosticos=diagnosticos,
      most_probable=most_probable,
      context_note=context_note,
      history=history or [],
    )

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
      try:
        response = await self.client.chat.completions.create(
          model="llama-3.3-70b-versatile",
          messages=messages,
          temperature=0.4,
        )
        return response.choices[0].message.content or ""
      except Exception as e:
        last_error = e
        if attempt < MAX_RETRIES:
          await asyncio.sleep(INITIAL_BACKOFF * (2 ** attempt))

    raise last_error or Exception("Error desconocido en Groq")

  def _build_messages(
      self,
      user_message: str,
      symptoms: list[str],
      diagnosticos: list[str],
      most_probable: str | None,
      context_note: str,
      history: list[dict],
  ) -> list[dict]:
    system_content = SYSTEM_PROMPT.format(
      accumulated_symptoms=", ".join(symptoms) if symptoms else "ninguno",
      diagnosticos=", ".join(diagnosticos) if diagnosticos else "ninguna",
      most_probable=most_probable if most_probable else "ninguna",
      context_note=context_note,
    )

    messages: list[dict] = [{"role": "system", "content": system_content}]

    for entry in history:
      role = entry.get("role")
      content = entry.get("content")
      if role in ("user", "assistant") and content:
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    return messages

groq_service = GroqService()
