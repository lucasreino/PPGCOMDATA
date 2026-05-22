"""
Remove dados extraídos do PDF/IA; mantém apenas registros xml_lattes.

Uso:
  python -m app.cleanup_pdf_data
  python -m app.cleanup_pdf_data --dry-run
  python -m app.cleanup_pdf_data --professor-email odlinari
"""

from __future__ import annotations

import argparse
import os
import sys

from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload
from app.services.upload_cleanup import delete_pdf_sourced_data
from app.services.upload_status import refresh_upload_validation_status


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove extrações PDF/IA; mantém dados XML Lattes"
    )
    parser.add_argument("--dry-run", action="store_true", help="Só conta, não apaga")
    parser.add_argument("--professor-email", type=str, default=None)
    parser.add_argument("--upload-id", type=str, default=None)
    args = parser.parse_args()

    with Session(engine) as session:
        professor_id = None
        if args.professor_email:
            prof = session.exec(
                select(Professor).where(
                    Professor.email.ilike(f"%{args.professor_email}%")
                )
            ).first()
            if not prof:
                print("Professor não encontrado.")
                sys.exit(1)
            professor_id = str(prof.id)
            print(f"Professor: {prof.nome_completo}")

        if args.dry_run:
            from app.models.enums import FonteDado
            from app.services.upload_cleanup import _MODELS_WITH_FONTE

            total = 0
            for model in _MODELS_WITH_FONTE:
                stmt = select(model).where(model.fonte_dado == FonteDado.PDF_LATTES)  # type: ignore
                if args.upload_id and hasattr(model, "curriculo_upload_id"):
                    stmt = stmt.where(model.curriculo_upload_id == args.upload_id)
                elif professor_id and hasattr(model, "professor_id"):
                    stmt = stmt.where(model.professor_id == professor_id)
                n = len(session.exec(stmt).all())
                if n:
                    print(f"  {model.__tablename__}: {n}")
                    total += n
            print(f"Total pdf_lattes (dry-run): {total}")
            return

        counts = delete_pdf_sourced_data(
            session,
            upload_id=args.upload_id,
            professor_id=professor_id,
        )
        print("Removidos:", counts)
        print(f"Total removido: {sum(counts.values())}")

        upload_ids: set[str] = set()
        if args.upload_id:
            upload_ids.add(args.upload_id)
        elif professor_id:
            for u in session.exec(
                select(CurriculoUpload).where(
                    CurriculoUpload.professor_id == professor_id
                )
            ).all():
                upload_ids.add(str(u.id))
        else:
            for u in session.exec(select(CurriculoUpload)).all():
                upload_ids.add(str(u.id))

        for uid in upload_ids:
            refresh_upload_validation_status(session, uid)

        print(f"Status de upload atualizado: {len(upload_ids)} upload(s).")


if __name__ == "__main__":
    main()
