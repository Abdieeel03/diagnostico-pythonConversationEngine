"""initial schema: chat memory in postgres

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-03 00:00:00

Crea el esquema completo de memoria de chat:
  - ENUM remitente_tipo
  - sintoma_catalogo
  - chat_session + trigger updated_at
  - chat_message
  - chat_symptom
  - chat_diagnostic
  - índices
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = '0001_initial'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


REMITENTE_ENUM = postgresql.ENUM('user', 'assistant', name='remitente_tipo', create_type=False)


def upgrade() -> None:
  remitente_tipo = postgresql.ENUM('user', 'assistant', name='remitente_tipo', create_type=True)
  remitente_tipo.create(op.get_bind(), checkfirst=True)

  op.create_table(
    'sintoma_catalogo',
    sa.Column('sintoma_key', sa.String(length=64), primary_key=True),
    sa.Column('descripcion', sa.String(length=255), nullable=False),
  )

  op.create_table(
    'chat_session',
    sa.Column('session_id', sa.BigInteger(), primary_key=True, autoincrement=True),
    sa.Column('client_id', sa.String(length=64), nullable=False),
    sa.Column(
      'titulo',
      sa.String(length=255),
      nullable=False,
      server_default=sa.text("'Nueva Consulta'"),
    ),
    sa.Column(
      'created_at',
      sa.DateTime(timezone=False),
      nullable=False,
      server_default=sa.text('NOW()'),
    ),
    sa.Column(
      'updated_at',
      sa.DateTime(timezone=False),
      nullable=False,
      server_default=sa.text('NOW()'),
    ),
    sa.UniqueConstraint('client_id', 'created_at', name='uq_chat_session_client_created'),
  )
  op.create_index(
    'idx_chat_session_client',
    'chat_session',
    ['client_id', sa.text('created_at DESC')],
  )

  op.execute(
    """
    CREATE OR REPLACE FUNCTION trg_set_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
      NEW.updated_at = NOW();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql
    """
  )
  op.execute(
    """
    CREATE TRIGGER chat_session_set_updated_at
    BEFORE UPDATE ON chat_session
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at()
    """
  )

  op.create_table(
    'chat_message',
    sa.Column('message_id', sa.BigInteger(), primary_key=True, autoincrement=True),
    sa.Column(
      'session_id',
      sa.BigInteger(),
      sa.ForeignKey('chat_session.session_id', ondelete='CASCADE'),
      nullable=False,
    ),
    sa.Column('remitente', REMITENTE_ENUM, nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('client_msg_id', sa.String(length=64), nullable=True),
    sa.Column(
      'created_at',
      sa.DateTime(timezone=False),
      nullable=False,
      server_default=sa.text('NOW()'),
    ),
  )
  op.create_index(
    'idx_chat_message_session_time',
    'chat_message',
    ['session_id', 'created_at'],
  )

  op.create_table(
    'chat_symptom',
    sa.Column('symptom_id', sa.BigInteger(), primary_key=True, autoincrement=True),
    sa.Column(
      'message_id',
      sa.BigInteger(),
      sa.ForeignKey('chat_message.message_id', ondelete='CASCADE'),
      nullable=False,
    ),
    sa.Column(
      'sintoma_key',
      sa.String(length=64),
      sa.ForeignKey('sintoma_catalogo.sintoma_key'),
      nullable=False,
    ),
    sa.Column(
      'created_at',
      sa.DateTime(timezone=False),
      nullable=False,
      server_default=sa.text('NOW()'),
    ),
  )
  op.create_index('idx_chat_symptom_message', 'chat_symptom', ['message_id'])
  op.create_index('idx_chat_symptom_key', 'chat_symptom', ['sintoma_key'])

  op.create_table(
    'chat_diagnostic',
    sa.Column('diagnostic_id', sa.BigInteger(), primary_key=True, autoincrement=True),
    sa.Column(
      'session_id',
      sa.BigInteger(),
      sa.ForeignKey('chat_session.session_id', ondelete='CASCADE'),
      nullable=False,
    ),
    sa.Column(
      'message_id',
      sa.BigInteger(),
      sa.ForeignKey('chat_message.message_id', ondelete='SET NULL'),
      nullable=True,
    ),
    sa.Column('enfermedad', sa.String(length=255), nullable=False),
    sa.Column('score', sa.Numeric(precision=5, scale=4), nullable=False),
    sa.Column(
      'coincidencias',
      sa.Integer(),
      nullable=False,
      server_default=sa.text('0'),
    ),
    sa.Column(
      'created_at',
      sa.DateTime(timezone=False),
      nullable=False,
      server_default=sa.text('NOW()'),
    ),
    sa.CheckConstraint('score >= 0 AND score <= 1', name='ck_chat_diagnostic_score_range'),
    sa.CheckConstraint('coincidencias >= 0', name='ck_chat_diagnostic_coincidencias_nonneg'),
  )
  op.create_index(
    'idx_chat_diagnostic_session',
    'chat_diagnostic',
    ['session_id', sa.text('created_at DESC')],
  )
  op.create_index(
    'idx_chat_diagnostic_enfermedad',
    'chat_diagnostic',
    ['enfermedad'],
  )


def downgrade() -> None:
  op.drop_index('idx_chat_diagnostic_enfermedad', table_name='chat_diagnostic')
  op.drop_index('idx_chat_diagnostic_session', table_name='chat_diagnostic')
  op.drop_table('chat_diagnostic')

  op.drop_index('idx_chat_symptom_key', table_name='chat_symptom')
  op.drop_index('idx_chat_symptom_message', table_name='chat_symptom')
  op.drop_table('chat_symptom')

  op.drop_index('idx_chat_message_session_time', table_name='chat_message')
  op.drop_table('chat_message')

  op.execute('DROP TRIGGER IF EXISTS chat_session_set_updated_at ON chat_session')
  op.execute('DROP FUNCTION IF EXISTS trg_set_updated_at()')
  op.drop_index('idx_chat_session_client', table_name='chat_session')
  op.drop_table('chat_session')

  op.drop_table('sintoma_catalogo')

  op.execute('DROP TYPE IF EXISTS remitente_tipo')
