"""
Remove dados extraídos de uploads antigos de um docente, mantendo só o upload mais recente.
Uso: python -m app.cleanup_professor_uploads --email camilla.tavares@ufma.br
"""

from __future__ import annotations

import argparse

from sqlmodel import Session, select

from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload
from app.services.upload_cleanup import clear_upload_extraction_data
from app.services.upload_pipeline import run_full_pipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--reprocess-latest",
        action="store_true",
        help="Reprocessa o último PDF após a limpeza",
    )
    args = parser.parse_args()

    with Session(engine) as session:
        prof = session.exec(
            select(Professor).where(Professor.email == args.email)
        ).first()
        if not prof:
            print(f"Docente não encontrado: {args.email}")
            return

        uploads = session.exec(
            select(CurriculoUpload)
            .where(CurriculoUpload.professor_id == prof.id)
            .order_by(CurriculoUpload.data_upload.desc())
        ).all()

        if not uploads:
            print("Nenhum upload para este docente.")
            return

        latest = uploads[0]
        print(f"Docente: {prof.nome_completo}")
        print(f"Mantendo upload mais recente: {latest.arquivo_nome} ({latest.id})")

        removed = 0
        for upload in uploads[1:]:
            print(f"  Limpando: {upload.arquivo_nome} ({upload.id})")
            clear_upload_extraction_data(session, upload.id)
            removed += 1

        print(f"Uploads limpos (dados IA removidos): {removed}")

        if args.reprocess_latest:
            print(f"Reprocessando: {latest.arquivo_nome}...")
            result = run_full_pipeline(session, latest.id)
            print("Resultado:", result)


if __name__ == "__main__":
    main()
