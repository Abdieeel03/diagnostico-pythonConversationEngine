from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
  AsyncEngine,
  AsyncSession,
  async_sessionmaker,
  create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.config.settings import settings


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
  global _engine
  if _engine is None:
    _engine = create_async_engine(
      settings.database_url,
      echo=False,
      poolclass=NullPool,
    )
  return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
  global _sessionmaker
  if _sessionmaker is None:
    _sessionmaker = async_sessionmaker(
      bind=get_engine(),
      class_=AsyncSession,
      expire_on_commit=False,
      autoflush=False,
    )
  return _sessionmaker


async def dispose_engine() -> None:
  global _engine, _sessionmaker
  if _engine is not None:
    await _engine.dispose()
  _engine = None
  _sessionmaker = None


async def get_db() -> AsyncIterator[AsyncSession]:
  async with get_sessionmaker()() as session:
    yield session
