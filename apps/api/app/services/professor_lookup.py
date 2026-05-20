"""Busca e normalização de docentes para evitar cadastros duplicados."""

from __future__ import annotations

import unicodedata
from typing import Optional

from sqlmodel import Session, select

from app.models.core import Professor


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFD", value.strip())
    without_accents = "".join(
        c for c in decomposed if unicodedata.category(c) != "Mn"
    )
    return " ".join(without_accents.lower().split())


def normalize_lattes_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return value.rstrip("/").split("/")[-1]


def professor_dedupe_key(prof: Professor) -> str:
    email = normalize_text(prof.email)
    if email:
        return f"email:{email}"
    lattes = normalize_lattes_id(prof.id_lattes)
    if lattes:
        return f"lattes:{lattes}"
    return f"nome:{normalize_text(prof.nome_completo)}"


def find_professor(
    session: Session,
    *,
    nome_completo: Optional[str] = None,
    email: Optional[str] = None,
    id_lattes: Optional[str] = None,
    candidates: Optional[list[Professor]] = None,
) -> Optional[Professor]:
    profs = candidates if candidates is not None else list(session.exec(select(Professor)).all())

    email_norm = normalize_text(email)
    lattes_norm = normalize_lattes_id(id_lattes)
    nome_norm = normalize_text(nome_completo)

    for p in profs:
        if email_norm and normalize_text(p.email) == email_norm:
            return p
    for p in profs:
        if lattes_norm and normalize_lattes_id(p.id_lattes) == lattes_norm:
            return p
    for p in profs:
        if nome_norm and normalize_text(p.nome_completo) == nome_norm:
            return p

    return None
