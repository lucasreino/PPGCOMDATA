"""
Reprocessa o último PDF Lattes de cada docente cadastrado.
Execute: python -m app.reprocess_all_curriculos [--delay 4] [--professor-delay 8]
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload
from app.models.enums import StatusProcessamento
from app.services.ai_extractor import extract_and_save_section_data
from app.services.pdf_processor import process_curriculo_pdf
from app.services.section_detector import split_and_save_sections
from app.services.upload_cleanup import clear_upload_extraction_data
from app.services.upload_status import refresh_upload_validation_status


def reprocess_upload(session: Session, upload_id: str, section_delay: float) -> dict:
    upload = process_curriculo_pdf(session, upload_id)
    if upload.status == StatusProcessamento.ERRO_NO_PROCESSAMENTO:
        return {"status": "erro", "mensagem": upload.mensagem_erro}

    sections = split_and_save_sections(session, upload_id)
    if not sections:
        upload.status = StatusProcessamento.PROCESSADO_COM_ALERTAS
        session.add(upload)
        session.commit()
        return {
            "status": "sucesso_com_alertas",
            "secoes_detectadas": 0,
            "extração_ia": {},
        }

    clear_upload_extraction_data(session, upload_id)

    ai_metrics = {
        "projetos_extraidos": 0,
        "eventos_extraidos": 0,
        "producoes_extraidas": 0,
        "financiamentos_extraidos": 0,
        "formacoes_extraidas": 0,
        "orientacoes_extraidas": 0,
        "bancas_extraidas": 0,
        "perfis_extraidos": 0,
        "producoes_tecnicas_extraidas": 0,
        "premios_extraidos": 0,
        "grupos_extraidos": 0,
        "lacunas_extraidas": 0,
    }

    for idx, section in enumerate(sections):
        try:
            metrics = extract_and_save_section_data(session, section.id)
            for key in ai_metrics:
                ai_metrics[key] += metrics.get(key, 0)
        except Exception as exc:
            print(f"    ⚠️ Seção '{section.nome_secao}': {exc}")
        if section_delay > 0 and idx < len(sections) - 1:
            time.sleep(section_delay)

    refresh_upload_validation_status(session, upload_id)
    session.refresh(upload)

    return {
        "status": "sucesso",
        "secoes_detectadas": len(sections),
        "extração_ia": ai_metrics,
    }


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
    args = parser.parse_args()

    print("=" * 60)
    print("PPGCOMDATA — Reprocessamento em lote (último PDF por docente)")
    print(f"Pausa entre seções: {args.delay}s | entre docentes: {args.professor_delay}s")
    print("=" * 60)

    ok = skip = fail = 0

    with Session(engine) as session:
        profs = session.exec(
            select(Professor).order_by(Professor.nome_completo)
        ).all()

        for i, prof in enumerate(profs, start=1):
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
                print(
                    f"    ✓ {result.get('status')} | seções={result.get('secoes_detectadas', 0)} | "
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
