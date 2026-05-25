"""
Reprocessa o último PDF Lattes de cada docente cadastrado.
Execute: python -m app.reprocess_all_curriculos [--delay 4] [--professor-delay 8]
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from sqlmodel import Session, select, func

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload, Producao
from app.services.upload_pipeline import run_full_pipeline


def reprocess_upload(session: Session, upload_id: str, section_delay: float) -> dict:
    """Reprocessa um upload com o mesmo pipeline da API (PDF + XML + reconciliação)."""
    del section_delay  # legado: paralelismo substitui pausa entre seções
    return run_full_pipeline(session, upload_id, xml_only_if_available=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reprocessa todos os Lattes")
    parser.add_argument(
        "--delay",
        type=float,
        default=4.0,
        help="Pausa extra entre seções (além do delay global da API)",
    )
    parser.add_argument(
        "--professor-delay",
        type=float,
        default=10.0,
        help="Pausa entre docentes",
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="Processar apenas o docente com este e-mail",
    )
    parser.add_argument(
        "--from-index",
        type=int,
        default=1,
        help="Índice 1-based do primeiro docente (ex.: 3 pula os dois primeiros)",
    )
    parser.add_argument(
        "--only-zero-producao",
        action="store_true",
        help="Reprocessar só docentes com zero registros em Producao",
    )
    args = parser.parse_args()

    print("=" * 60)
    from app.config import settings

    print("PPGCOMDATA — Reprocessamento em lote (último PDF por docente)")
    print(
        f"IA paralela: {settings.AI_PARALLEL_WORKERS} workers | "
        f"chunk ≤{settings.SECTION_CHUNK_MAX_CHARS} chars | "
        f"entre docentes: {args.professor_delay}s"
    )
    print("=" * 60)

    ok = skip = fail = 0

    with Session(engine) as session:
        stmt = select(Professor).order_by(Professor.nome_completo)
        if args.email:
            stmt = stmt.where(Professor.email == args.email)
        profs = session.exec(stmt).all()
        if not profs:
            print(f"Nenhum docente com e-mail {args.email}" if args.email else "Nenhum docente encontrado")
            return

        if args.only_zero_producao:
            filtered: list[Professor] = []
            for prof in profs:
                count = session.exec(
                    select(func.count())
                    .select_from(Producao)
                    .where(Producao.professor_id == prof.id)
                ).one()
                if count == 0:
                    filtered.append(prof)
            profs = filtered
            print(f"Filtro --only-zero-producao: {len(profs)} docente(s)")

        for i, prof in enumerate(profs, start=1):
            if i < args.from_index:
                print(f"[{i}/{len(profs)}] SKIP {prof.nome_completo} (--from-index)")
                skip += 1
                continue
            upload = session.exec(
                select(CurriculoUpload)
                .where(CurriculoUpload.professor_id == prof.id)
                .order_by(CurriculoUpload.data_upload.desc())
            ).first()

            if not upload:
                print(f"[{i}/{len(profs)}] SKIP {prof.nome_completo} — sem PDF")
                skip += 1
                continue

            print(f"[{i}/{len(profs)}] {prof.nome_completo} ({upload.arquivo_nome})")
            try:
                result = reprocess_upload(session, upload.id, args.delay)
                metrics = result.get("extração_ia") or {}
                xml = result.get("importacao_xml") or {}
                rec = result.get("reconciliacao") or {}
                rec_totais = rec.get("totais") or {}
                print(
                    f"    ✓ {result.get('status')} | seções={result.get('secoes_detectadas', 0)} | "
                    f"xml={bool(xml.get('xml_importado'))} | "
                    f"xml_confirmados={rec_totais.get('xml_confirmados', 0)} | "
                    f"pdf_descartados={rec_totais.get('pdf_descartados', 0)} | "
                    f"orientações={metrics.get('orientacoes_extraidas', 0)} | "
                    f"produções={metrics.get('producoes_extraidas', 0)}"
                )
                ok += 1
            except Exception as exc:
                print(f"    ✗ ERRO: {exc}")
                session.rollback()
                fail += 1

            if args.professor_delay > 0 and i < len(profs):
                time.sleep(args.professor_delay)

    print("=" * 60)
    print(f"Concluído: {ok} reprocessados, {skip} sem PDF, {fail} com erro")
    print("=" * 60)


if __name__ == "__main__":
    main()
