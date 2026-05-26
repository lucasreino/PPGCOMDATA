"""
Importa apenas grupos de pesquisa dos XMLs Lattes (heurística em PROJETO-DE-PESQUISA).

Uso:
  python -m app.import_grupos_lattes_xml_batch
  python -m app.import_grupos_lattes_xml_batch --xml-dir /caminho/xml
  python -m app.import_grupos_lattes_xml_batch --dry-run
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
from app.routes.dossie_apcn import invalidate_dossie_cache
from app.services.grupo_pesquisa_lattes import (
    import_grupos_from_atuacoes_xml,
)
from app.services.lattes_xml_importer import _attr, _find_first, _load_xml_root, _trecho_xml
from app.services.professor_lookup import normalize_lattes_id
from app.models.enums import ConfiancaIA, FonteDado

_XML_SOURCE = FonteDado.XML_LATTES
_XML_CONF = ConfiancaIA.ALTA


def _latest_upload(session: Session, professor_id: str) -> CurriculoUpload | None:
    return session.exec(
        select(CurriculoUpload)
        .where(CurriculoUpload.professor_id == professor_id)
        .order_by(CurriculoUpload.data_upload.desc())
    ).first()


def import_grupos_from_xml_path(
    session: Session,
    upload: CurriculoUpload,
    xml_path: Path,
) -> int:
    root = _load_xml_root(xml_path)
    atuacoes = _find_first(
        root,
        "ATUACOES-PROFISSIONAIS",
        "DADOS-GERAIS/ATUACOES-PROFISSIONAIS",
    )
    if atuacoes is None:
        return 0
    return import_grupos_from_atuacoes_xml(
        session,
        upload,
        atuacoes,
        attr_fn=_attr,
        trecho_fn=_trecho_xml,
        fonte=_XML_SOURCE,
        confianca=_XML_CONF,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa grupos de pesquisa dos XMLs Lattes")
    parser.add_argument("--xml-dir", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    xml_dir = Path(args.xml_dir or settings.LATTES_XML_DIR or "")
    if not xml_dir.is_dir():
        print(f"Pasta XML inválida: {xml_dir}")
        sys.exit(1)

    xml_files = sorted(xml_dir.glob("*.xml"))
    total_grupos = 0
    ok = 0
    skipped = 0

    with Session(engine) as session:
        profs = session.exec(select(Professor)).all()
        by_lattes = {
            normalize_lattes_id(p.id_lattes): p
            for p in profs
            if normalize_lattes_id(p.id_lattes)
        }

        for path in xml_files:
            lid = path.stem
            prof = by_lattes.get(lid)
            if not prof:
                skipped += 1
                continue
            upload = _latest_upload(session, prof.id)
            if not upload:
                skipped += 1
                continue

            if args.dry_run:
                print(f"[dry] {path.name} → {prof.nome_completo}")
                ok += 1
                continue

            n = import_grupos_from_xml_path(session, upload, path)
            if n:
                print(f"[grupos] {prof.nome_completo}: +{n}")
            total_grupos += n
            ok += 1

        session.commit()

    invalidate_dossie_cache()
    print(
        f"Concluído: {ok} XMLs, {skipped} ignorados, "
        f"{total_grupos} grupo(s) novo(s) importado(s)."
    )


if __name__ == "__main__":
    main()
