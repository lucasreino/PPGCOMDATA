"""
Corrige vínculo PDF → docente e cria uploads faltantes a partir de data/lattes.
Execute: python -m app.fix_upload_assignments
"""

from __future__ import annotations

import os
import shutil
import sys
import uuid

from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload
from app.models.enums import StatusProcessamento
from app.services.upload_assignment import (
    _FILENAME_RULES,
    normalize_filename,
    reassign_upload_record,
    resolve_professor_for_filename,
)
from app.utils_fix_linhas import PROFESSOR_DATA

if os.path.exists("/workspace/data/lattes"):
    LATTES_SRC_DIR = "/workspace/data/lattes"
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    LATTES_SRC_DIR = os.path.join(ROOT, "data", "lattes")


def _expected_filename_hint(email: str) -> str:
    for data in PROFESSOR_DATA:
        if data["email"].lower() == email.lower():
            return normalize_filename(data["nome_completo"])
    return ""


def fix_existing_uploads(session: Session) -> dict:
    profs = list(session.exec(select(Professor)).all())
    uploads = list(session.exec(select(CurriculoUpload)).all())
    moved = 0
    deleted = 0

    for upload in uploads:
        target = resolve_professor_for_filename(session, upload.arquivo_nome or "", profs)
        if not target:
            print(f"  ? Sem match: {upload.arquivo_nome}")
            continue
        if upload.professor_id != target.id:
            print(f"  → {upload.arquivo_nome} → {target.nome_completo}")
            reassign_upload_record(session, upload, target.id)
            moved += 1

    session.commit()

    # Um upload canônico por docente (arquivo cujo nome melhor corresponde ao docente)
    profs = list(session.exec(select(Professor)).all())
    for prof in profs:
        prof_uploads = session.exec(
            select(CurriculoUpload).where(CurriculoUpload.professor_id == prof.id)
        ).all()
        if len(prof_uploads) <= 1:
            continue

        hint = _expected_filename_hint(prof.email or "")

        def score_upload(u: CurriculoUpload) -> int:
            name = normalize_filename(u.arquivo_nome or "")
            s = 0
            if hint and any(part in name for part in hint.split() if len(part) > 3):
                s += 10
            for needle, rule_email in _FILENAME_RULES:
                if rule_email == (prof.email or "").lower() and needle in name:
                    s += 5
            return s

        ranked = sorted(prof_uploads, key=score_upload, reverse=True)
        keep = ranked[0]
        for extra in ranked[1:]:
            session.delete(extra)
            deleted += 1
            print(f"  ✕ Removido duplicata de {prof.nome_completo}: {extra.arquivo_nome}")

    session.commit()
    return {"moved": moved, "deleted_duplicates": deleted}


def create_missing_uploads(session: Session) -> int:
    if not os.path.isdir(LATTES_SRC_DIR):
        print(f"Pasta não encontrada: {LATTES_SRC_DIR}")
        return 0

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    profs = list(session.exec(select(Professor)).all())
    created = 0

    for filename in sorted(os.listdir(LATTES_SRC_DIR)):
        if not filename.lower().endswith(".pdf"):
            continue

        target = resolve_professor_for_filename(session, filename, profs)
        if not target:
            print(f"  ? PDF sem docente: {filename}")
            continue

        existing = session.exec(
            select(CurriculoUpload)
            .where(CurriculoUpload.professor_id == target.id)
            .where(CurriculoUpload.arquivo_nome == filename)
        ).first()
        if existing:
            continue

        dest_name = f"{uuid.uuid4()}.pdf"
        dest_path = os.path.join(settings.UPLOAD_DIR, dest_name)
        shutil.copy2(os.path.join(LATTES_SRC_DIR, filename), dest_path)

        upload = CurriculoUpload(
            professor_id=target.id,
            arquivo_url=dest_path,
            arquivo_nome=filename,
            status=StatusProcessamento.AGUARDANDO_PROCESSAMENTO,
        )
        session.add(upload)
        created += 1
        print(f"  + Criado upload para {target.nome_completo}: {filename}")

    session.commit()
    return created


def main() -> None:
    print("=" * 60)
    print("PPGCOMDATA — Correção de vínculo PDF → docente")
    print("=" * 60)

    with Session(engine) as session:
        print("\n--- Reatribuindo uploads existentes ---")
        stats = fix_existing_uploads(session)
        print(f"  Movidos: {stats['moved']} | Duplicatas removidas: {stats['deleted_duplicates']}")

        print("\n--- Criando uploads faltantes (data/lattes) ---")
        created = create_missing_uploads(session)
        print(f"  Novos uploads: {created}")

    print("\n--- Concluído! Rode: python -m app.reprocess_all_curriculos --delay 4")
    print("=" * 60)


if __name__ == "__main__":
    main()
