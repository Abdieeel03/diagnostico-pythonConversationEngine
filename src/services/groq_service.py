import asyncio

from groq import AsyncGroq

from src.config.settings import settings

MAX_RETRIES = 2
INITIAL_BACKOFF = 1.0
REQUEST_TIMEOUT = 30.0

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
      context_note: str
  ) -> str:
    prompt = self._build_prompt(
      user_message, symptoms, diagnosticos, most_probable, context_note
    )

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
      try:
        response = await self.client.chat.completions.create(
          model="llama-3.3-70b-versatile",
          messages=[
            {
              "role": "user",
              "content": prompt
            }
          ],
          temperature=0.4,
        )
        return response.choices[0].message.content or ""
      except Exception as e:
        last_error = e
        if attempt < MAX_RETRIES:
          await asyncio.sleep(INITIAL_BACKOFF * (2 ** attempt))

    raise last_error or Exception("Error desconocido en Groq")

  def _build_prompt(
      self,
      user_message: str,
      symptoms: list[str],
      diagnosticos: list[str],
      most_probable: str | None,
      context_note: str
  ) -> str:
    return f"""
Eres un asistente conversacional de orientación médica.

Mensaje original del usuario:
{user_message}

Síntomas detectados:
{", ".join(symptoms)}

Posibles enfermedades identificadas:
{", ".join(diagnosticos) if diagnosticos else "ninguna"}

Enfermedad con mayor compatibilidad:
{most_probable if most_probable else "ninguna"}

Contexto adicional:
{context_note}

Instrucciones:

- Responde en español.
- Usa un tono cercano y natural.
- No menciones motores expertos, algoritmos, scores, porcentajes ni coincidencias.
- No expliques cómo se obtuvo el resultado.
- No inventes enfermedades que no aparezcan en la lista.
- No inventes síntomas ni tratamientos.
- No digas que es un diagnóstico definitivo.
- Explica brevemente cuál es la enfermedad más compatible y menciona otras posibilidades si existen.
- Finaliza indicando que se trata de una orientación y que ante síntomas persistentes debe consultarse a un profesional de salud.
- Si hay pocos síntomas, responde máximo en 1 párrafo.
- Máximo 2 párrafos.
- No repitas varias veces que debe consultar a un profesional.

MUY IMPORTANTE:
Si no existe una enfermedad principal, no menciones enfermedades específicas
como posibles causas.

Limítate a indicar que la información es insuficiente y solicita más síntomas.
"""

groq_service = GroqService()