from src.services.nlp_service import nlp_service
from src.services.prolog_service import prolog_service
from src.services.groq_service import groq_service

DEFAULT_SESSION_ID = "default"

class _SessionStore:
  def __init__(self):
    self._sessions: dict[str, dict] = {}

  def get_or_create(self, session_id: str) -> dict:
    if session_id not in self._sessions:
      self._sessions[session_id] = {
        "symptoms": [],
        "history": [],
      }
    return self._sessions[session_id]

  def get(self, session_id: str) -> dict | None:
    return self._sessions.get(session_id)


session_store = _SessionStore()


class DiagnosisService:
  async def process_message(self, message: str, session_id: str | None = None):
    sid = session_id or DEFAULT_SESSION_ID
    session = session_store.get_or_create(sid)

    new_symptoms = nlp_service.extract_symptoms(message)
    accumulated_symptoms = self._merge_symptoms(session["symptoms"], new_symptoms)
    session["symptoms"] = accumulated_symptoms

    if not accumulated_symptoms:
      session["history"].append({"role": "user", "content": message})
      response_text = "No pude identificar síntomas claros en tu mensaje. Intenta describir como te sientes con más detalle."
      session["history"].append({"role": "assistant", "content": response_text})
      self._trim_history(session)
      return {
        "response": response_text,
        "symptoms": [],
        "diagnosticos": [],
        "most_probable": None,
      }

    prolog_response = await prolog_service.get_diagnostico(accumulated_symptoms)

    session["history"].append({"role": "user", "content": message})

    if not prolog_response.get("success"):
      response_text = "No pude obtener un diagnóstico en este momento."
      session["history"].append({"role": "assistant", "content": response_text})
      self._trim_history(session)
      return {
        "response": response_text,
        "symptoms": accumulated_symptoms,
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

    diagnosticos = self._filter_diagnosticos(diagnosticos, accumulated_symptoms)

    most_probable = self._get_most_probable(diagnosticos, accumulated_symptoms)

    context_note = self._get_context_note(accumulated_symptoms, most_probable)

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
      symptoms=accumulated_symptoms,
      diagnosticos=diagnosticos_names,
      most_probable=most_probable_name,
      context_note=context_note,
      history=session["history"][:-1],
    )

    session["history"].append({"role": "assistant", "content": response_text})
    self._trim_history(session)

    return {
      "response": response_text,
      "symptoms": accumulated_symptoms,
      "diagnosticos": diagnosticos,
      "most_probable": most_probable,
    }

  def _merge_symptoms(self, existing: list[str], new: list[str]) -> list[str]:
    merged = list(existing)
    for s in new:
      if s not in merged:
        merged.append(s)
    return merged

  def _trim_history(self, session: dict, max_pairs: int = 6) -> None:
    history = session["history"]
    if len(history) > max_pairs * 2:
      session["history"] = history[-(max_pairs * 2):]

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
