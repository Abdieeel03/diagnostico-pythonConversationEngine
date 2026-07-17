from collections.abc import AsyncIterator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import (
  AsyncEngine,
  AsyncSession,
  async_sessionmaker,
  create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.config.settings import settings


_SSLMODE_TO_ASYNCPG = {
  'disable': False,
  'allow': 'allow',
  'prefer': 'prefer',
  'require': 'require',
  'verify-ca': 'verify-ca',
  'verify-full': 'verify-full',
}


def _adapt_url_for_asyncpg(database_url: str) -> tuple[str, dict]:
  parsed = urlparse(database_url)
  query = parse_qs(parsed.query, keep_blank_values=True)

  if 'sslmode' not in query:
    return database_url, {}

  sslmode = query['sslmode'][0]
  if sslmode not in _SSLMODE_TO_ASYNCPG:
    return database_url, {}

  ssl_value = _SSLMODE_TO_ASYNCPG[sslmode]
  del query['sslmode']

  new_query = urlencode(query, doseq=True)
  clean_parsed = parsed._replace(query=new_query)
  clean_url = urlunparse(clean_parsed)

  connect_args: dict = {'ssl': ssl_value}
  return clean_url, connect_args


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
  global _engine
  if _engine is None:
    clean_url, connect_args = _adapt_url_for_asyncpg(settings.database_url)
    _engine = create_async_engine(
      clean_url,
      echo=False,
      poolclass=NullPool,
      connect_args=connect_args,
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
