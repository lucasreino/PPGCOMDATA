"""Associa uploads de PDF ao docente correto pelo nome do arquivo."""

from __future__ import annotations

import os
import re
from typing import Optional

from sqlmodel import Session, select

from app.models.core import Professor
from app.models.data import CurriculoUpload, PdfPage, PdfSection
from app.services.professor_lookup import find_professor, normalize_text
from app.utils_fix_linhas import PROFESSOR_DATA

# Ordem importa: padrões mais específicos primeiro
_FILENAME_RULES: list[tuple[str, str]] = [
    ("camilla", "camilla.tavares@ufma.br"),
    ("tavares", "camilla.tavares@ufma.br"),
    ("izani", "izani.mustafa@ufma.br"),
    ("mustafa", "izani.mustafa@ufma.br"),
    ("messias", "jose.cmsf@ufma.br"),
    ("jose carlos", "jose.cmsf@ufma.br"),
    ("larissa", "larissa.leda@ufma.br"),
    ("marcelli", "marcelli.alves@ufma.br"),
    ("domingos", "domingos.almeida@ufma.br"),
    ("odlinari", "odlinari.silva@ufma.br"),
    ("ramon nascimento", "odlinari.silva@ufma.br"),
    ("nascimento da silva", "odlinari.silva@ufma.br"),
    ("gislene", "maria.gcf@ufma.br"),
    ("gisa", "maria.gcf@ufma.br"),
    ("leila", "sousa.leila@ufma.br"),
    ("leticia", "leticia.cardoso@ufma.br"),
    ("thaisa", "thaisa.bueno@ufma.br"),
    ("thays", "thays.assuncao@ufma.br"),
    ("michelly", "michelly.carvalho@ufma.br"),
]


def normalize_filename(filename: str) -> str:
    base = os.path.splitext(filename or "")[0]
    base = re.sub(r"[_\-]+", " ", base)
    return normalize_text(base)


def resolve_email_from_filename(filename: str) -> Optional[str]:
    norm = normalize_filename(filename)
    for needle, email in _FILENAME_RULES:
        if needle in norm:
            return email
    return None


def resolve_professor_for_filename(
    session: Session, filename: str, profs: Optional[list[Professor]] = None
) -> Optional[Professor]:
    email = resolve_email_from_filename(filename)
    if not email:
        return None
    official = next((d for d in PROFESSOR_DATA if d["email"].lower() == email.lower()), None)
    return find_professor(
        session,
        email=email,
        nome_completo=official["nome_completo"] if official else None,
        id_lattes=official.get("id_lattes") if official else None,
        candidates=profs,
    )


def reassign_upload_record(
    session: Session, upload: CurriculoUpload, professor_id: str
) -> None:
    upload.professor_id = professor_id
    session.add(upload)

    pages = session.exec(
        select(PdfPage).where(PdfPage.curriculo_upload_id == upload.id)
    ).all()
    for page in pages:
        page.professor_id = professor_id
        session.add(page)

    sections = session.exec(
        select(PdfSection).where(PdfSection.curriculo_upload_id == upload.id)
    ).all()
    for section in sections:
        section.professor_id = professor_id
        session.add(section)
