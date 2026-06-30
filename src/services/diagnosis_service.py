from src.services.nlp_service import nlp_service
from src.services.prolog_service import prolog_service
from src.services.groq_service import groq_service

class DiagnosisService:
  async def process_message(self, message: str):
    symptoms = nlp_service.extract_symptoms(message)

    if not symptoms:
      return {
        "response": "No pude identificar síntomas claros en tu mensaje. Intenta describir como te sientes con más detalle.",
        "symptoms": [],
        "diagnosticos": [],
        "most_probable": None,
      }

    prolog_response = await prolog_service.get_diagnostico(symptoms)

    if not prolog_response.get("success"):
      return {
        "response": "No pude obtener un diagnóstico en este momento.",
        "symptoms": symptoms,
        "diagnosticos": [],
        "most_probable": None,
      }
    
    data = prolog_response.get("data")

    if not isinstance(data, dict):
      data = {}

    diagnosticos = data.get("diagnosticos", [])

    diagnosticos = sorted(
      diagnosticos, 
      key=lambda d: d.get("score", 0), 
      reverse=True
    )

    diagnosticos = self._filter_diagnosticos(diagnosticos, symptoms)

    most_probable = self._get_most_probable(diagnosticos, symptoms)

    context_note = self._get_context_note(symptoms, most_probable)

    diagnosticos_names = [
      d["enfermedad"]
      for d in diagnosticos
    ]

    most_probable_name = (
      most_probable["enfermedad"]
      if most_probable
      else None
    )

    response_text = await groq_service.generate_response(
      user_message=message,
      symptoms=symptoms,
      diagnosticos=diagnosticos_names,
      most_probable=most_probable_name,
      context_note=context_note
    )

    return {
      "response": response_text,
      "symptoms": symptoms,
      "diagnosticos": diagnosticos,
      "most_probable": most_probable,
    }

  def _filter_diagnosticos(self, diagnosticos: list[dict], symptoms: list[str]) -> list[dict]:
    symptoms_count = len(symptoms)

    if symptoms_count <= 1:
        return diagnosticos[:3]

    if symptoms_count == 2:
        return diagnosticos[:5]

    return [
        d for d in diagnosticos
        if d.get("coincidencias", 0) >= 2
    ][:5]
  
  def _get_most_probable(self, diagnosticos: list[dict], symptoms: list[str]):
    if len(symptoms) <= 1:
        return None

    return diagnosticos[0] if diagnosticos else None
  
  def _get_context_note(self, symptoms: list[str], most_probable):
    if len(symptoms) <= 1:
        return (
            "Hay muy pocos síntomas para orientar una enfermedad. "
            "No menciones enfermedades específicas. "
            "Solicita más síntomas al usuario."
        )

    if most_probable is None:
        return (
            "No hay suficiente información para orientar una enfermedad principal. "
            "Pide al usuario más detalles."
        )

    return (
        "Puedes mencionar la enfermedad con mayor compatibilidad, "
        "pero sin decir scores, porcentajes ni coincidencias."
    )

diagnosis_service = DiagnosisService()