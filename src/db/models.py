from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
  BigInteger,
  CheckConstraint,
  DateTime,
  ForeignKey,
  Index,
  Integer,
  Numeric,
  String,
  Text,
  UniqueConstraint,
  func,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
  pass


class Remitente(str, PyEnum):
  USER = 'user'
  ASSISTANT = 'assistant'


class SintomaCatalogo(Base):
  __tablename__ = 'sintoma_catalogo'

  sintoma_key: Mapped[str] = mapped_column(String(64), primary_key=True)
  descripcion: Mapped[str] = mapped_column(String(255), nullable=False)


class ChatSession(Base):
  __tablename__ = 'chat_session'
  __table_args__ = (
    UniqueConstraint('client_id', 'created_at', name='uq_chat_session_client_created'),
    Index('idx_chat_session_client', 'client_id', 'created_at'),
  )

  session_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
  client_id: Mapped[str] = mapped_column(String(64), nullable=False)
  titulo: Mapped[str] = mapped_column(String(255), nullable=False, default='Nueva Consulta')
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=False), nullable=False, server_default=func.now()
  )
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=False), nullable=False, server_default=func.now()
  )

  messages: Mapped[list['ChatMessage']] = relationship(
    back_populates='session',
    cascade='all, delete-orphan',
    order_by='ChatMessage.created_at',
  )
  diagnostics: Mapped[list['ChatDiagnostic']] = relationship(
    back_populates='session',
    cascade='all, delete-orphan',
    order_by='ChatDiagnostic.created_at',
  )


class ChatMessage(Base):
  __tablename__ = 'chat_message'
  __table_args__ = (
    Index('idx_chat_message_session_time', 'session_id', 'created_at'),
  )

  message_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
  session_id: Mapped[int] = mapped_column(
    BigInteger,
    ForeignKey('chat_session.session_id', ondelete='CASCADE'),
    nullable=False,
  )
  remitente: Mapped[Remitente] = mapped_column(
    PG_ENUM(Remitente, name='remitente_tipo', create_type=False, values_callable=lambda e: [m.value for m in e]),
    nullable=False,
  )
  content: Mapped[str] = mapped_column(Text, nullable=False)
  client_msg_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=False), nullable=False, server_default=func.now()
  )

  session: Mapped[ChatSession] = relationship(back_populates='messages')
  symptoms: Mapped[list['ChatSymptom']] = relationship(
    back_populates='message',
    cascade='all, delete-orphan',
  )


class ChatSymptom(Base):
  __tablename__ = 'chat_symptom'
  __table_args__ = (
    Index('idx_chat_symptom_message', 'message_id'),
    Index('idx_chat_symptom_key', 'sintoma_key'),
  )

  symptom_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
  message_id: Mapped[int] = mapped_column(
    BigInteger,
    ForeignKey('chat_message.message_id', ondelete='CASCADE'),
    nullable=False,
  )
  sintoma_key: Mapped[str] = mapped_column(
    String(64),
    ForeignKey('sintoma_catalogo.sintoma_key'),
    nullable=False,
  )
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=False), nullable=False, server_default=func.now()
  )

  message: Mapped[ChatMessage] = relationship(back_populates='symptoms')


class ChatDiagnostic(Base):
  __tablename__ = 'chat_diagnostic'
  __table_args__ = (
    CheckConstraint('score >= 0 AND score <= 1', name='ck_chat_diagnostic_score_range'),
    CheckConstraint('coincidencias >= 0', name='ck_chat_diagnostic_coincidencias_nonneg'),
    Index('idx_chat_diagnostic_session', 'session_id', 'created_at'),
    Index('idx_chat_diagnostic_enfermedad', 'enfermedad'),
  )

  diagnostic_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
  session_id: Mapped[int] = mapped_column(
    BigInteger,
    ForeignKey('chat_session.session_id', ondelete='CASCADE'),
    nullable=False,
  )
  message_id: Mapped[int | None] = mapped_column(
    BigInteger,
    ForeignKey('chat_message.message_id', ondelete='SET NULL'),
    nullable=True,
  )
  enfermedad: Mapped[str] = mapped_column(String(255), nullable=False)
  score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
  coincidencias: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=False), nullable=False, server_default=func.now()
  )

  session: Mapped[ChatSession] = relationship(back_populates='diagnostics')
