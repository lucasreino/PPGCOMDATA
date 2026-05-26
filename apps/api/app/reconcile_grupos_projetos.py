"""
Reclassifica projetos que são grupos de pesquisa (fase 4).

Uso:
  python -m app.reconcile_grupos_projetos
  python -m app.reconcile_grupos_projetos --dry-run
  python -m app.reconcile_grupos_projetos --professor-id <uuid>
"""

from __future__ import annotations

import argparse
import os
import sys

from sqlmodel import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.routes.dossie_apcn import invalidate_dossie_cache
from app.services.grupo_projeto_reconcile import reconcile_projetos_misclassified_as_grupos


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Move projetos-grupo para grupos_pesquisa_docente e descarta duplicata"
    )
    parser.add_argument("--professor-id", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with Session(engine) as session:
        metrics = reconcile_projetos_misclassified_as_grupos(
            session,
            professor_id=args.professor_id,
            dry_run=args.dry_run,
        )

    if not args.dry_run:
        invalidate_dossie_cache()

    print(metrics)


if __name__ == "__main__":
    main()
