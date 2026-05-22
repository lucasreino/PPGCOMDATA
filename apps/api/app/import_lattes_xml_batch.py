"""
Importa XML Lattes em lote para o último upload de cada docente (por id_lattes).

Uso:
  set LATTES_XML_DIR=C:\\Users\\...\\lattes-xml\\output
  python -m app.import_lattes_xml_batch
  python -m app.import_lattes_xml_batch --reprocess
  python -m app.import_lattes_xml_batch --xml-dir "C:\\path\\to\\output"
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
from app.services.upload_pipeline import run_full_pipeline
from app.services.upload_status import refresh_upload_validation_status


def _latest_upload(session: Session, professor_id: str) -> CurriculoUpload | None:
    return session.exec(
        select(CurriculoUpload)
        .where(CurriculoUpload.professor_id == professor_id)
        .order_by(CurriculoUpload.data_upload.desc())
    ).first()


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa XML Lattes em lote")
    parser.add_argument(
        "--xml-dir",
        type=str,
        default=None,
        help="Pasta com arquivos {id_lattes}.xml (default: LATTES_XML_DIR)",
    )
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="Reprocessa upload: PDF (texto/seções) + importação XML, sem IA",
    )
    parser.add_argument(
        "--reprocess-ai",
        action="store_true",
        help="(legado) Igual a --reprocess",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas lista correspondências, sem gravar",
    )
    args = parser.parse_args()

    xml_dir = Path(args.xml_dir or settings.LATTES_XML_DIR or "")
    if not xml_dir.is_dir():
        print(f"Pasta XML inválida: {xml_dir}")
        sys.exit(1)

    xml_files = sorted(xml_dir.glob("*.xml"))
    if not xml_files:
        print(f"Nenhum .xml em {xml_dir}")
        sys.exit(0)

    with Session(engine) as session:
        profs = session.exec(select(Professor)).all()
        by_lattes = {
            normalize_lattes_id(p.id_lattes): p
            for p in profs
            if normalize_lattes_id(p.id_lattes)
        }

        ok = 0
        skipped = 0
        for path in xml_files:
            lid = path.stem
            prof = by_lattes.get(lid)
            if not prof:
                print(f"[skip] {path.name}: professor id_lattes={lid} não cadastrado")
                skipped += 1
                continue
            upload = _latest_upload(session, prof.id)
            if not upload:
                print(f"[skip] {path.name}: {prof.nome_completo} sem upload PDF")
                skipped += 1
                continue

            if args.dry_run:
                print(f"[dry] {path.name} → {prof.nome_completo} upload={upload.id}")
                ok += 1
                continue

            if args.reprocess or args.reprocess_ai:
                print(f"[pipeline] {prof.nome_completo} ({lid})")
                os.environ.setdefault("LATTES_XML_DIR", str(xml_dir))
                settings.LATTES_XML_DIR = str(xml_dir)
                result = run_full_pipeline(session, upload.id, xml_only_if_available=True)
                print(
                    f"  {result.get('status')} xml={result.get('importacao_xml')} "
                    f"somente_xml={result.get('modo_somente_xml')}"
                )
            else:
                clear_upload_extraction_data(session, upload.id)
                metrics = import_lattes_xml(session, upload.id, path)
                mark_xml_covered_sections_extracted(session, upload.id)
                from app.services.upload_cleanup import mark_all_sections_extracted

                mark_all_sections_extracted(session, upload.id)
                refresh_upload_validation_status(session, upload.id)
                print(f"[xml] {prof.nome_completo}: {metrics}")
            ok += 1

    print(f"Concluído: {ok} processados, {skipped} ignorados, {len(xml_files)} arquivos.")


if __name__ == "__main__":
    main()
