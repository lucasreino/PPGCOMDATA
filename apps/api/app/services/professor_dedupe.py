"""Funde registros duplicados de professores e reatribui dados vinculados."""

from __future__ import annotations

from typing import Dict, List, Type

from sqlmodel import Session, SQLModel, select

from app.models.core import Professor
from app.models.data import (
    AlertaLacuna,
    Banca,
    CurriculoUpload,
    Evento,
    Financiamento,
    FormacaoAcademica,
    GrupoPesquisaDocente,
    Orientacao,
    PdfPage,
    PdfSection,
    PerfilLattes,
    PremioTitulo,
    Producao,
    ProducaoTecnica,
    Projeto,
)
from app.services.professor_lookup import professor_dedupe_key


_MODELS_WITH_PROFESSOR_ID: List[Type[SQLModel]] = [
    CurriculoUpload,
    PdfPage,
    PdfSection,
    Projeto,
    Evento,
    Producao,
    Financiamento,
    AlertaLacuna,
    FormacaoAcademica,
    Orientacao,
    Banca,
    PerfilLattes,
    ProducaoTecnica,
    PremioTitulo,
    GrupoPesquisaDocente,
]


def _upload_count(session: Session, professor_id: str) -> int:
    return len(
        session.exec(
            select(CurriculoUpload).where(CurriculoUpload.professor_id == professor_id)
        ).all()
    )


def _pick_canonical_with_session(session: Session, group: List[Professor]) -> Professor:
    return max(
        group,
        key=lambda p: (
            bool(p.email),
            bool(p.id_lattes),
            _upload_count(session, p.id),
            bool(p.linha_pesquisa_id),
            len(p.nome_completo or ""),
        ),
    )


def _reassign_professor_id(session: Session, old_id: str, new_id: str) -> None:
    for model in _MODELS_WITH_PROFESSOR_ID:
        rows = session.exec(select(model).where(model.professor_id == old_id)).all()  # type: ignore[attr-defined]
        for row in rows:
            row.professor_id = new_id  # type: ignore[attr-defined]
            session.add(row)


def merge_duplicate_professors(session: Session) -> Dict[str, int]:
    """Mescla professores com mesmo e-mail, ID Lattes ou nome normalizado."""
    profs = list(session.exec(select(Professor)).all())
    groups: Dict[str, List[Professor]] = {}
    for prof in profs:
        groups.setdefault(professor_dedupe_key(prof), []).append(prof)

    merged = 0
    deleted = 0
    for group in groups.values():
        if len(group) <= 1:
            continue
        canonical = _pick_canonical_with_session(session, group)
        for dup in group:
            if dup.id == canonical.id:
                continue
            _reassign_professor_id(session, dup.id, canonical.id)
            session.delete(dup)
            merged += 1
            deleted += 1

    if deleted:
        session.commit()

    return {"groups_merged": merged, "records_deleted": deleted}
