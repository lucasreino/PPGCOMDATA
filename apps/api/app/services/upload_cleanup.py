"""Remove AI-extracted records tied to an upload before reprocessing."""

from sqlmodel import Session, select

from app.models.data import (
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
    PdfSection,
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
