"""
Verifica se o perfil Scholar do Lucas (ou --scholar-user) foi aplicado no banco.

Exit 0 = OK; exit 1 = perfil não vinculado ou sem citações em produções.
"""

from __future__ import annotations

import argparse
import os
import sys

from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.core import Professor
from app.models.data import Producao
from app.services.professor_lookup import normalize_lattes_id

DEFAULT_LATTES = "5487269670962081"
DEFAULT_SCHOLAR_USER = "Q61X3XUAAAAJ"


def main() -> None:
    parser = argparse.ArgumentParser(description="Verifica sync Google Scholar no banco")
    parser.add_argument("--id-lattes", default=DEFAULT_LATTES)
    parser.add_argument("--scholar-user", default=DEFAULT_SCHOLAR_USER)
    parser.add_argument("--min-citations-rows", type=int, default=1)
    args = parser.parse_args()

    lid = normalize_lattes_id(args.id_lattes) or ""
    with Session(engine) as session:
        prof = next(
            (
                p
                for p in session.exec(select(Professor)).all()
                if normalize_lattes_id(p.id_lattes) == lid
                or p.scholar_user_id == args.scholar_user
            ),
            None,
        )
        if not prof:
            print(
                f"ERRO: docente não encontrado (id_lattes={args.id_lattes}, "
                f"scholar_user={args.scholar_user})",
                file=sys.stderr,
            )
            sys.exit(1)

        producoes = list(
            session.exec(select(Producao).where(Producao.professor_id == prof.id)).all()
        )
        with_citations = [p for p in producoes if p.scholar_citations is not None]

        print(f"professor_id={prof.id}")
        print(f"nome={prof.nome_completo}")
        print(f"scholar_user_id={prof.scholar_user_id}")
        print(f"scholar_citations_total={prof.scholar_citations_total}")
        print(f"scholar_h_index={prof.scholar_h_index}")
        print(f"producoes_total={len(producoes)}")
        print(f"producoes_com_citacoes_scholar={len(with_citations)}")

        ok = (
            prof.scholar_user_id == args.scholar_user
            and prof.scholar_citations_total is not None
            and len(with_citations) >= args.min_citations_rows
        )
        if not ok:
            print("ERRO: perfil Scholar não aplicado corretamente.", file=sys.stderr)
            sys.exit(1)

        print("OK: perfil Scholar vinculado e citações gravadas em produções.")


if __name__ == "__main__":
    main()
