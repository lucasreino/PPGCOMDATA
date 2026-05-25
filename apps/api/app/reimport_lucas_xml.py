"""
Reimporta XML Lattes para Lucas Reino (id_lattes 5487269670962081).

Uso:
  python -m app.reimport_lucas_xml
  python -m app.reimport_lucas_xml --xml-path C:\\path\\5487269670962081.xml
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload
from app.services.lattes_xml_importer import (
    import_lattes_xml,
    mark_xml_covered_sections_extracted,
)
from app.services.professor_lookup import normalize_lattes_id
from app.services.upload_cleanup import clear_upload_extraction_data
from app.services.upload_status import refresh_upload_validation_status
from app.services.xml_pdf_reconciler import reconcile_upload_xml_pdf

LUCAS_LATTES_ID = "5487269670962081"


def main() -> None:
    parser = argparse.ArgumentParser(description="Reimporta XML Lattes do Lucas")
    parser.add_argument(
        "--xml-path",
        type=str,
        default=None,
        help=f"Caminho do XML (default: LATTES_XML_DIR/{LUCAS_LATTES_ID}.xml)",
    )
    args = parser.parse_args()

    xml_path = args.xml_path
    if not xml_path:
        base = settings.LATTES_XML_DIR or ""
        xml_path = os.path.join(base, f"{LUCAS_LATTES_ID}.xml")
    if not os.path.isfile(xml_path):
        print(f"XML não encontrado: {xml_path}")
        sys.exit(1)

    with Session(engine) as session:
        prof = session.exec(
            select(Professor).where(
                Professor.id_lattes == normalize_lattes_id(LUCAS_LATTES_ID)
            )
        ).first()
        if not prof:
            prof = session.exec(
                select(Professor).where(Professor.nome_completo.ilike("%lucas%"))
            ).first()
        if not prof:
            print("Professor Lucas não encontrado no banco.")
            sys.exit(1)

        upload = session.exec(
            select(CurriculoUpload)
            .where(CurriculoUpload.professor_id == str(prof.id))
            .order_by(CurriculoUpload.data_upload.desc())
        ).first()
        if not upload:
            print("Nenhum upload para Lucas.")
            sys.exit(1)

        print(f"Professor: {prof.nome_completo} ({prof.id_lattes})")
        print(f"Upload: {upload.id}")
        print(f"XML: {xml_path}")

        clear_upload_extraction_data(session, str(upload.id))
        metrics = import_lattes_xml(session, str(upload.id), xml_path)
        marked = mark_xml_covered_sections_extracted(session, str(upload.id))
        reconcile = reconcile_upload_xml_pdf(
            session,
            str(upload.id),
            xml_dir=str(Path(xml_path).parent),
        )
        refresh_upload_validation_status(session, str(upload.id))
        print(f"Métricas: {metrics}")
        print(f"Seções marcadas (sem IA): {marked}")
        print(f"Reconciliação: {reconcile.to_dict()}")


if __name__ == "__main__":
    main()
