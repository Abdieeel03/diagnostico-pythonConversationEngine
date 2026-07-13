from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import (
  ChatDiagnostic,
  ChatMessage,
  ChatSession,
  ChatSymptom,
  Remitente,
  SintomaCatalogo,
)


class ChatRepository:
  def __init__(self, session: AsyncSession):
    self.session = session

  async def get_or_create_session(
    self, client_id: str, titulo: str = 'Nueva Consulta'
  ) -> ChatSession:
    """Devuelve la sesión más reciente del client_id. Si no existe, crea una nueva."""
    stmt = (
      select(ChatSession)
      .where(ChatSession.client_id == client_id)
      .order_by(ChatSession.created_at.desc())
      .limit(1)
    )
    result = await self.session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
      return existing

    new_session = ChatSession(client_id=client_id, titulo=titulo)
    self.session.add(new_session)
    await self.session.flush()
    return new_session

  async def update_session_title(self, session_id: int, titulo: str) -> None:
    session = await self.session.get(ChatSession, session_id)
    if session is not None:
      session.titulo = titulo
      await self.session.flush()

  async def get_message_by_client_id(
    self, session_id: int, client_msg_id: str
  ) -> ChatMessage | None:
    if not client_msg_id:
      return None
    stmt = (
      select(ChatMessage)
      .where(ChatMessage.session_id == session_id)
      .where(ChatMessage.client_msg_id == client_msg_id)
      .options(selectinload(ChatMessage.symptoms))
      .limit(1)
    )
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()

  async def add_user_message(
    self,
    session_id: int,
    content: str,
    client_msg_id: str | None = None,
    symptoms: list[str] | None = None,
  ) -> ChatMessage:
    message = ChatMessage(
      session_id=session_id,
      remitente=Remitente.USER,
      content=content,
      client_msg_id=client_msg_id,
    )
    self.session.add(message)
    await self.session.flush()

    for sintoma_key in symptoms or []:
      self.session.add(
        ChatSymptom(message_id=message.message_id, sintoma_key=sintoma_key)
      )
    if symptoms:
      await self.session.flush()

    return message

  async def add_assistant_message(
    self, session_id: int, content: str
  ) -> ChatMessage:
    message = ChatMessage(
      session_id=session_id,
      remitente=Remitente.ASSISTANT,
      content=content,
    )
    self.session.add(message)
    await self.session.flush()
    return message

  async def add_diagnostics(
    self,
    session_id: int,
    message_id: int,
    diagnosticos: list[dict],
  ) -> list[ChatDiagnostic]:
    """diagnosticos: lista de {enfermedad, score, coincidencias}"""
    rows: list[ChatDiagnostic] = []
    for d in diagnosticos:
      row = ChatDiagnostic(
        session_id=session_id,
        message_id=message_id,
        enfermedad=d['enfermedad'],
        score=Decimal(str(d['score'])),
        coincidencias=int(d.get('coincidencias', 0)),
      )
      self.session.add(row)
      rows.append(row)
    if rows:
      await self.session.flush()
    return rows

  async def load_recent_history(
    self, session_id: int, max_pairs: int = 6
  ) -> list[dict]:
    """Devuelve los últimos N turnos (user/assistant) en orden cronológico."""
    stmt = (
      select(ChatMessage)
      .where(ChatMessage.session_id == session_id)
      .order_by(ChatMessage.created_at.desc())
      .limit(max_pairs * 2)
    )
    result = await self.session.execute(stmt)
    messages = list(reversed(result.scalars().all()))
    return [
      {'role': m.remitente.value, 'content': m.content}
      for m in messages
    ]

  async def get_session_symptoms(self, session_id: int) -> list[str]:
    """Devuelve la lista única de síntomas detectados en la sesión hasta ahora."""
    stmt = (
      select(ChatSymptom.sintoma_key)
      .join(ChatMessage, ChatMessage.message_id == ChatSymptom.message_id)
      .where(ChatMessage.session_id == session_id)
      .group_by(ChatSymptom.sintoma_key)
    )
    result = await self.session.execute(stmt)
    return [row[0] for row in result.all()]

  async def get_known_symptom_keys(self) -> set[str]:
    """Devuelve el conjunto de claves de síntomas en el catálogo.
    Útil para filtrar síntomas NLP antes de guardarlos."""
    stmt = select(SintomaCatalogo.sintoma_key)
    result = await self.session.execute(stmt)
    return {row[0] for row in result.all()}

  async def ensure_session_loaded(self, session_id: int) -> ChatSession | None:
    stmt = (
      select(ChatSession)
      .where(ChatSession.session_id == session_id)
      .options(
        selectinload(ChatSession.messages).selectinload(ChatMessage.symptoms),
        selectinload(ChatSession.diagnostics),
      )
    )
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()
