"""
Sincroniza grupos de pesquisa a partir do cadastro oficial (observacoes dos docentes).

Uso:
  python -m app.backfill_grupos_pesquisa
  python -m app.backfill_grupos_pesquisa --professor-id <uuid>
"""

from __future__ import annotations

import argparse
import os
import sys

from sqlmodel import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.routes.dossie_apcn import invalidate_dossie_cache
from app.services.grupos_pesquisa_sync import sync_grupos_from_observacoes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill grupos_pesquisa_docente a partir de observacoes"
    )
    parser.add_argument("--professor-id", type=str, default=None)
    args = parser.parse_args()

    with Session(engine) as session:
        metrics = sync_grupos_from_observacoes(session, professor_id=args.professor_id)

    invalidate_dossie_cache()
    print(metrics)


if __name__ == "__main__":
    main()
