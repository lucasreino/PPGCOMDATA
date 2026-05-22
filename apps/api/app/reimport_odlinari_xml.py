"""
Reimporta XML Lattes apenas para Odlinari (id_lattes 4303555424897191).

Uso:
  set LATTES_XML_DIR=C:\\Users\\...\\lattes-xml\\output
  python -m app.reimport_odlinari_xml
  python -m app.reimport_odlinari_xml --xml-path C:\\path\\4303555424897191.xml
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
from app.services.xml_pdf_reconciler import reconcile_upload_xml_pdf
from app.services.professor_lookup import normalize_lattes_id
from app.services.upload_cleanup import clear_upload_extraction_data

ODLINARI_LATTES_ID = "4303555424897191"


def main() -> None:
    parser = argparse.ArgumentParser(description="Reimporta XML Lattes do Odlinari")
    parser.add_argument(
        "--xml-path",
        type=str,
        default=None,
        help="Caminho do XML (default: LATTES_XML_DIR/4303555424897191.xml)",
    )
    args = parser.parse_args()

    xml_path = args.xml_path
    if not xml_path:
        base = settings.LATTES_XML_DIR or ""
        xml_path = os.path.join(base, f"{ODLINARI_LATTES_ID}.xml")
    if not os.path.isfile(xml_path):
        print(f"XML não encontrado: {xml_path}")
        sys.exit(1)

    with Session(engine) as session:
        prof = session.exec(
            select(Professor).where(
                Professor.id_lattes == normalize_lattes_id(ODLINARI_LATTES_ID)
            )
        ).first()
        if not prof:
            prof = session.exec(
                select(Professor).where(Professor.email.ilike("%odlinari%"))
            ).first()
        if not prof:
            print("Professor Odlinari não encontrado no banco.")
            sys.exit(1)

        upload = session.exec(
            select(CurriculoUpload)
            .where(CurriculoUpload.professor_id == str(prof.id))
            .order_by(CurriculoUpload.data_upload.desc())
        ).first()
        if not upload:
            print("Nenhum upload para Odlinari.")
            sys.exit(1)

        print(f"Professor: {prof.nome_completo}")
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
        print(f"Métricas: {metrics}")
        print(f"Seções marcadas (sem IA): {marked}")
        print(f"Reconciliação: {reconcile.to_dict()}")


if __name__ == "__main__":
    main()
