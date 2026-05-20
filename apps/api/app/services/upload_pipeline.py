"""Pipeline completo de processamento de um upload Lattes."""

from __future__ import annotations

import logging

from sqlmodel import Session

from app.database import engine
from app.models.data import CurriculoUpload
from app.models.enums import StatusProcessamento
from app.services.ai_extractor import extract_and_save_section_data
from app.services.pdf_processor import process_curriculo_pdf
from app.services.section_detector import split_and_save_sections
from app.services.upload_cleanup import clear_upload_extraction_data
from app.services.upload_status import refresh_upload_validation_status

logger = logging.getLogger("ppgcomdata.upload_pipeline")


def run_full_pipeline(session: Session, upload_id: str) -> dict:
    """Extrai PDF, detecta seções e roda IA (síncrono, para uso em rota ou background)."""
    upload = process_curriculo_pdf(session, upload_id)
    if upload.status == StatusProcessamento.ERRO_NO_PROCESSAMENTO:
        return {"status": "erro", "mensagem": upload.mensagem_erro}

    sections = split_and_save_sections(session, upload_id)
    if not sections:
        upload.status = StatusProcessamento.PROCESSADO_COM_ALERTAS
        session.add(upload)
        session.commit()
        return {
            "status": "sucesso_com_alertas",
            "mensagem": "Texto extraído, mas nenhuma seção relevante foi identificada.",
            "secoes_detectadas": 0,
            "extração_ia": {},
        }

    clear_upload_extraction_data(session, upload_id)

    ai_metrics = {
        "projetos_extraidos": 0,
        "eventos_extraidos": 0,
        "producoes_extraidas": 0,
        "financiamentos_extraidos": 0,
        "formacoes_extraidas": 0,
        "orientacoes_extraidas": 0,
        "bancas_extraidas": 0,
        "perfis_extraidos": 0,
        "producoes_tecnicas_extraidas": 0,
        "premios_extraidos": 0,
        "grupos_extraidos": 0,
        "lacunas_extraidas": 0,
    }

    for section in sections:
        try:
            metrics = extract_and_save_section_data(session, section.id)
            for key in ai_metrics:
                ai_metrics[key] += metrics.get(key, 0)
        except Exception as exc:
            logger.error("Erro na seção %s: %s", section.nome_secao, exc)

    refresh_upload_validation_status(session, upload_id)
    session.refresh(upload)

    return {
        "status": "sucesso",
        "upload_status": upload.status.value if hasattr(upload.status, "value") else str(upload.status),
        "secoes_detectadas": len(sections),
        "extração_ia": ai_metrics,
    }


def run_full_pipeline_background(upload_id: str) -> None:
    """Executa o pipeline em thread de background (sessão própria)."""
    with Session(engine) as session:
        try:
            run_full_pipeline(session, upload_id)
        except Exception as exc:
            logger.exception("Falha no pipeline em background para %s: %s", upload_id, exc)
            upload = session.get(CurriculoUpload, upload_id)
            if upload:
                upload.status = StatusProcessamento.ERRO_NO_PROCESSAMENTO
                upload.mensagem_erro = str(exc)[:500]
                session.add(upload)
                session.commit()
