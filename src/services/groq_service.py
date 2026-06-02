from groq import Groq

from src.config.settings import settings

class GroqService:
  def __init__(self):
    self.client = Groq(
      api_key=settings.groq_api_key
    )
  
  def generate_response(
      self,
      user_message: str,
      symptoms: list[str],
      diagnosticos: list[dict],
      most_probable: dict | None
  ) -> str:
    prompt = f"""
Eres un asistente conversacional de orientación médica.

Mensaje original del usuario:
{user_message}

Síntomas detectados:
{symptoms}

Posibles enfermedades identificadas:
{", ".join(d["enfermedad"] for d in diagnosticos)}

Enfermedad con mayor compatibilidad:
{most_probable["enfermedad"] if most_probable else "ninguna"}

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
- Máximo 2 párrafos.
"""
    response = self.client.chat.completions.create(
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
  
groq_service = GroqService()