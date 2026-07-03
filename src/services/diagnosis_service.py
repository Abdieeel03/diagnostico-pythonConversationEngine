from src.services.nlp_service import nlp_service
from src.services.prolog_service import prolog_service
from src.services.groq_service import groq_service
from src.repositories.chat_repository import ChatRepository
from src.db.session import get_sessionmaker


FALLBACK_NO_SYMPTOMS = (
  "No pude identificar sintomas claros en tu mensaje. "
  "Intenta describir como te sientes con mas detalle."
)
FALLBACK_PROLOG_ERROR = "No pude obtener un diagnostico en este momento."


class DiagnosisService:
  async def process_message(
    self,
    message: str,
    client_id: str,
    client_msg_id: str | None = None,
  ) -> dict:
    """Procesa un mensaje del usuario, persistiendo todo en la DB.

    `client_id` es el identificador que manda el frontend (session_id del localStorage).
    `client_msg_id` es el id del mensaje del usuario, para idempotencia en reintentos.
    """
    async with get_sessionmaker()() as db:
      repo = ChatRepository(db)

      session = await repo.get_or_create_session(client_id=client_id)
      session_id = session.session_id

      if client_msg_id:
        cached = await repo.get_message_by_client_id(session_id, client_msg_id)
        if cached is not None:
          cached_symptoms = [s.sintoma_key for s in cached.symptoms]
          await db.commit()
          return {
            'session_id': session_id,
            'response': '',
            'symptoms': cached_symptoms,
            'diagnosticos': [],
            'most_probable': None,
            'duplicate': True,
          }

      known_symptoms = await repo.get_known_symptom_keys()
      new_symptoms = nlp_service.extract_symptoms(message)
      filtered_new = [s for s in new_symptoms if s in known_symptoms]

      history = await repo.load_recent_history(session_id, max_pairs=6)
      previous_symptoms = await repo.get_session_symptoms(session_id)
      accumulated_symptoms = self._merge_symptoms(previous_symptoms, filtered_new)

      user_msg = await repo.add_user_message(
        session_id=session_id,
        content=message,
        client_msg_id=client_msg_id,
        symptoms=filtered_new,
      )

      if not accumulated_symptoms:
        response_text = FALLBACK_NO_SYMPTOMS
        await repo.add_assistant_message(session_id=session_id, content=response_text)
        await db.commit()
        return self._build_payload(
          session_id=session_id,
          response=response_text,
          symptoms=[],
          diagnosticos=[],
          most_probable=None,
        )

      prolog_response = await prolog_service.get_diagnostico(accumulated_symptoms)

      if not prolog_response.get('success'):
        response_text = FALLBACK_PROLOG_ERROR
        await repo.add_assistant_message(session_id=session_id, content=response_text)
        await db.commit()
        return self._build_payload(
          session_id=session_id,
          response=response_text,
          symptoms=accumulated_symptoms,
          diagnosticos=[],
          most_probable=None,
        )

      data = prolog_response.get('data') or {}
      diagnosticos = sorted(
        data.get('diagnosticos', []),
        key=lambda d: d.get('score', 0),
        reverse=True,
      )
      diagnosticos = self._filter_diagnosticos(diagnosticos, accumulated_symptoms)
      most_probable = self._get_most_probable(diagnosticos, accumulated_symptoms)
      context_note = self._get_context_note(accumulated_symptoms, most_probable)

      diagnosticos_names = [d['enfermedad'] for d in diagnosticos]
      most_probable_name = most_probable['enfermedad'] if most_probable else None

      history_for_llm = history

      try:
        response_text = await groq_service.generate_response(
          user_message=message,
          symptoms=accumulated_symptoms,
          diagnosticos=diagnosticos_names,
          most_probable=most_probable_name,
          context_note=context_note,
          history=history_for_llm,
        )
      except Exception:
        response_text = (
          "Tuve un problema al generar la respuesta, pero registre tus sintomas. "
          "Intentalo de nuevo en un momento."
        )

      await repo.add_assistant_message(session_id=session_id, content=response_text)

      if diagnosticos:
        await repo.add_diagnostics(
          session_id=session_id,
          message_id=user_msg.message_id,
          diagnosticos=diagnosticos,
        )

      await db.commit()

      return self._build_payload(
        session_id=session_id,
        response=response_text,
        symptoms=accumulated_symptoms,
        diagnosticos=diagnosticos,
        most_probable=most_probable,
      )

  def _build_payload(
    self,
    session_id: int,
    response: str,
    symptoms: list[str],
    diagnosticos: list[dict],
    most_probable: dict | None,
  ) -> dict:
    return {
      'session_id': session_id,
      'response': response,
      'symptoms': symptoms,
      'diagnosticos': diagnosticos,
      'most_probable': most_probable,
    }

  def _merge_symptoms(
    self, previous: list[str], new_symptoms: list[str]
  ) -> list[str]:
    merged: list[str] = list(previous)
    for s in new_symptoms:
      if s not in merged:
        merged.append(s)
    return merged

  def _filter_diagnosticos(
    self, diagnosticos: list[dict], symptoms: list[str]
  ) -> list[dict]:
    symptoms_count = len(symptoms)

    if symptoms_count <= 1:
      return diagnosticos[:3]

    if symptoms_count == 2:
      return diagnosticos[:5]

    return [
      d for d in diagnosticos if d.get('coincidencias', 0) >= 2
    ][:5]

  def _get_most_probable(
    self, diagnosticos: list[dict], symptoms: list[str]
  ) -> dict | None:
    if len(symptoms) <= 1:
      return None
    return diagnosticos[0] if diagnosticos else None

  def _get_context_note(self, symptoms: list[str], most_probable) -> str:
    if len(symptoms) <= 1:
      return (
        'Hay muy pocos sintomas para orientar una enfermedad. '
        'No menciones enfermedades especificas. '
        'Solicita mas sintomas al usuario.'
      )

    if most_probable is None:
      return (
        'No hay suficiente informacion para orientar una enfermedad principal. '
        'Pide al usuario mas detalles.'
      )

    return (
      'Puedes mencionar la enfermedad con mayor compatibilidad, '
      'pero sin decir scores, porcentajes ni coincidencias.'
    )


diagnosis_service = DiagnosisService()
