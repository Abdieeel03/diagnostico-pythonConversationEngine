import os
import sys
import uvicorn

from src.config.settings import settings


def _run_alembic_upgrade_head() -> None:
  from alembic import command
  from alembic.config import Config

  root = os.path.dirname(os.path.abspath(__file__))
  cfg = Config(os.path.join(root, 'alembic.ini'))
  cfg.set_main_option('script_location', os.path.join(root, 'alembic'))
  cfg.set_main_option('sqlalchemy.url', settings.database_url)
  print('[run] Ejecutando alembic upgrade head ...')
  command.upgrade(cfg, 'head')
  print('[run] Migraciones aplicadas.')


def _seed_if_empty_sync() -> None:
  import psycopg2
  from scripts.seed_symptoms import _parse_symptoms_from_prolog, _find_prolog_facts_path

  sync_url = settings.database_url.replace('postgresql+asyncpg://', 'postgresql://', 1)
  sync_url = sync_url.replace('postgresql+psycopg2://', 'postgresql://', 1)
  from urllib.parse import urlparse
  parsed = urlparse(sync_url)

  conn = psycopg2.connect(
    host=parsed.hostname,
    port=parsed.port or 5432,
    user=parsed.username,
    password=parsed.password,
    dbname=parsed.path.lstrip('/'),
  )
  conn.autocommit = True
  cur = conn.cursor()
  cur.execute('SELECT 1 FROM sintoma_catalogo LIMIT 1')
  if cur.fetchone() is not None:
    cur.close()
    conn.close()
    return
  print('[run] Catálogo de síntomas vacío, corriendo seed ...')
  cur.close()
  conn.close()

  catalogo = _parse_symptoms_from_prolog(_find_prolog_facts_path())
  conn = psycopg2.connect(
    host=parsed.hostname,
    port=parsed.port or 5432,
    user=parsed.username,
    password=parsed.password,
    dbname=parsed.path.lstrip('/'),
  )
  cur = conn.cursor()
  args = [(k, v) for k, v in catalogo.items()]
  from psycopg2.extras import execute_values
  execute_values(
    cur,
    'INSERT INTO sintoma_catalogo (sintoma_key, descripcion) VALUES %s ON CONFLICT (sintoma_key) DO NOTHING',
    args,
  )
  conn.commit()
  cur.close()
  conn.close()
  print(f'[run] Catálogo cargado: {len(catalogo)} síntomas.')


def _ensure_schema() -> None:
  if not settings.auto_migrate:
    print('[run] AUTO_MIGRATE=false, saltando migración inicial.')
    return
  try:
    _run_alembic_upgrade_head()
  except Exception as exc:
    print(f'[run] ERROR: no se pudieron aplicar las migraciones: {exc}', file=sys.stderr)
    sys.exit(1)
  try:
    _seed_if_empty_sync()
  except Exception as exc:
    print(f'[run] WARN: seed inicial falló: {exc}', file=sys.stderr)


if __name__ == '__main__':
  _ensure_schema()

  reload = os.getenv('RELOAD', '').lower() in ('true', '1', 'yes')
  uvicorn.run(
    'src.main:app',
    host='0.0.0.0',
    port=settings.port,
    reload=reload,
  )
