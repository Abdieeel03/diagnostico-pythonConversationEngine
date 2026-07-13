"""Alembic environment.

Usa la DATABASE_URL del settings de la app para conectarse, y los metadatos
de src.db.models.Base como target para autogenerate.

Alembic opera con engines síncronos, por lo que convierte la URL async
(postgresql+asyncpg://) a la variante sync (postgresql+psycopg2://) si es
necesario. Si ya viene una URL sync, la respeta.
"""
from __future__ import annotations

import re
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.config.settings import settings
from src.db.models import Base

config = context.config

if config.config_file_name is not None:
  fileConfig(config.config_file_name)


def _to_sync_url(url: str) -> str:
  if url.startswith('postgresql+asyncpg://'):
    return url.replace('postgresql+asyncpg://', 'postgresql+psycopg2://', 1)
  if url.startswith('sqlite+aiosqlite://'):
    return url.replace('sqlite+aiosqlite://', 'sqlite://', 1)
  return url


def _install_psycopg2_if_possible() -> None:
  try:
    import psycopg2  # noqa: F401
  except ImportError:
    pass


config.set_main_option('sqlalchemy.url', _to_sync_url(settings.database_url))
_install_psycopg2_if_possible()

target_metadata = Base.metadata


def run_migrations_offline() -> None:
  url = config.get_main_option('sqlalchemy.url')
  context.configure(
    url=url,
    target_metadata=target_metadata,
    literal_binds=True,
    dialect_opts={'paramstyle': 'named'},
  )
  with context.begin_transaction():
    context.run_migrations()


def run_migrations_online() -> None:
  connectable = engine_from_config(
    config.get_section(config.config_ini_section, {}),
    prefix='sqlalchemy.',
    poolclass=pool.NullPool,
  )
  with connectable.connect() as connection:
    context.configure(
      connection=connection,
      target_metadata=target_metadata,
      compare_type=True,
    )
    with context.begin_transaction():
      context.run_migrations()


if context.is_offline_mode():
  run_migrations_offline()
else:
  run_migrations_online()
