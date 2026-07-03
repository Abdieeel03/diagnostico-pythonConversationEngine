"""Seed del catálogo de síntomas desde el módulo Prolog.

Lee `diagnostico-prologEngine/src/knowledge/facts/sintomas.pl` y carga todos
los átomos únicos en la tabla `sintoma_catalogo`. Si el átomo ya existe, lo deja
igual (ON CONFLICT DO NOTHING).

Uso:
    python scripts/seed_symptoms.py
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from src.config.settings import settings
from src.db.models import SintomaCatalogo
from src.db.session import get_sessionmaker


def _find_prolog_facts_path() -> Path:
  here = Path(__file__).resolve().parent
  candidates = [
    here.parent.parent / 'diagnostico-prologEngine' / 'src' / 'knowledge' / 'facts' / 'sintomas.pl',
    Path('/app/diagnostico-prologEngine/src/knowledge/facts/sintomas.pl'),
    Path(os.getenv('PROLOG_FACTS_PATH', '')),
  ]
  for c in candidates:
    if c and c.is_file():
      return c
  raise FileNotFoundError(
    'No se encontró sintomas.pl. Definí PROLOG_FACTS_PATH o montá el submódulo Prolog.'
  )


def _parse_symptoms_from_prolog(path: Path) -> dict[str, str]:
  text = path.read_text(encoding='utf-8')
  pattern = re.compile(r"sintoma\(\s*\w+\s*,\s*([a-z_][a-z0-9_]*)\s*\)\s*\.")
  keys = set(pattern.findall(text))
  return {k: k.replace('_', ' ') for k in sorted(keys)}


async def seed() -> None:
  path = _find_prolog_facts_path()
  print(f'Leyendo síntomas de: {path}')
  catalogo = _parse_symptoms_from_prolog(path)
  print(f'Encontrados {len(catalogo)} síntomas únicos.')

  async with get_sessionmaker()() as session:
    stmt = insert(SintomaCatalogo).values(
      [{'sintoma_key': k, 'descripcion': v} for k, v in catalogo.items()]
    )
    stmt = stmt.on_conflict_do_nothing(index_elements=['sintoma_key'])
    await session.execute(stmt)
    await session.commit()
  print('Catálogo cargado OK.')


async def main() -> None:
  await seed()
  from src.db.session import dispose_engine
  await dispose_engine()


if __name__ == '__main__':
  try:
    asyncio.run(main())
  except Exception as exc:
    print(f'Error: {exc}', file=sys.stderr)
    sys.exit(1)
