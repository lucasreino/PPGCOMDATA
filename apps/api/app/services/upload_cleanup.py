"""Remove extrações e dados derivados de uploads antes de reprocessar."""

from __future__ import annotations

from typing import Any, Optional, Type

from sqlmodel import Session, SQLModel, select

from app.models.data import (
    AlertaLacuna,
    Banca,
    Evento,
    Financiamento,
    FormacaoAcademica,
    GrupoPesquisaDocente,
    Orientacao,
    PdfSection,
    PerfilLattes,
    PremioTitulo,
    Producao,
    ProducaoTecnica,
    Projeto,
)
from app.models.enums import FonteDado

_PDF = FonteDado.PDF_LATTES

_MODELS_WITH_FONTE: tuple[Type[SQLModel], ...] = (
    Projeto,
    Evento,
    Producao,
    Financiamento,
    FormacaoAcademica,
    Orientacao,
    Banca,
    PerfilLattes,
    ProducaoTecnica,
    PremioTitulo,
    GrupoPesquisaDocente,
)


def clear_upload_extraction_data(session: Session, upload_id: str) -> None:
    """Deletes derived entities for a curriculum upload (keeps pages/sections)."""
    models_with_upload = (
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
    )
    for model in models_with_upload:
        upload_col = model.__table__.c.get("curriculo_upload_id")
        if upload_col is None:
            continue
        rows = session.exec(select(model).where(upload_col == upload_id)).all()
        for row in rows:
            session.delete(row)

    sections = session.exec(
        select(PdfSection).where(PdfSection.curriculo_upload_id == upload_id)
    ).all()
    for section in sections:
        section.status_extracao = False
        session.add(section)

    session.commit()


def delete_pdf_sourced_data(
    session: Session,
    *,
    upload_id: Optional[str] = None,
    professor_id: Optional[str] = None,
    delete_lacunas: bool = True,
) -> dict[str, int]:
    """Remove registros extraídos do PDF/IA (fonte pdf_lattes), mantém XML."""
    counts: dict[str, int] = {}

    for model in _MODELS_WITH_FONTE:
        if not hasattr(model, "fonte_dado"):
            continue
        stmt = select(model).where(model.fonte_dado == _PDF)  # type: ignore[attr-defined]
        upload_col = model.__table__.c.get("curriculo_upload_id")  # type: ignore[union-attr]
        if upload_id and upload_col is not None:
            stmt = stmt.where(upload_col == str(upload_id))
        elif professor_id and hasattr(model, "professor_id"):
            stmt = stmt.where(model.professor_id == str(professor_id))  # type: ignore[attr-defined]
        rows = list(session.exec(stmt).all())
        label = getattr(model, "__tablename__", model.__name__)
        for row in rows:
            session.delete(row)
        if rows:
            counts[label] = len(rows)

    if delete_lacunas:
        lac_stmt = select(AlertaLacuna)
        if upload_id:
            lac_stmt = lac_stmt.where(
                AlertaLacuna.curriculo_upload_id == str(upload_id)
            )
        elif professor_id:
            lac_stmt = lac_stmt.where(AlertaLacuna.professor_id == str(professor_id))
        lacunas = list(session.exec(lac_stmt).all())
        for lac in lacunas:
            session.delete(lac)
        if lacunas:
            counts["alertas_lacunas"] = len(lacunas)

    session.commit()
    return counts


def mark_all_sections_extracted(session: Session, upload_id: str) -> int:
    """Marca todas as seções do upload como processadas (modo só XML)."""
    sections = session.exec(
        select(PdfSection).where(PdfSection.curriculo_upload_id == upload_id)
    ).all()
    for section in sections:
        section.status_extracao = True
        session.add(section)
    session.commit()
    return len(sections)
