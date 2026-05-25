"""Pipeline completo de processamento de um upload Lattes."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlmodel import Session, select

from app.config import settings
from app.database import engine
from app.models.data import CurriculoUpload, PdfSection
from app.models.enums import StatusProcessamento
from app.services.ai_extractor import extract_and_save_section_data
from app.services.lattes_xml_importer import (
    import_lattes_xml_if_available,
    mark_xml_covered_sections_extracted,
)
from app.services.pdf_processor import process_curriculo_pdf
from app.services.section_detector import split_and_save_sections
from app.services.upload_cleanup import (
    clear_upload_extraction_data,
    mark_all_sections_extracted,
)
from app.services.upload_status import refresh_upload_validation_status
from app.services.xml_pdf_reconciler import reconcile_upload_xml_pdf
from app.services.cache_invalidation import invalidate_indicator_caches
from app.services.qualis_catalog import apply_qualis_to_producoes

logger = logging.getLogger("ppgcomdata.upload_pipeline")


def _extract_section_worker(section_id: str) -> tuple[str, dict | None, str | None]:
    """Worker thread-safe: sessão SQL própria por seção."""
    try:
        with Session(engine) as session:
            metrics = extract_and_save_section_data(session, section_id)
            return section_id, metrics, None
    except Exception as exc:
        logger.exception("Erro na seção %s: %s", section_id, exc)
        return section_id, None, str(exc)


def run_full_pipeline(
    session: Session,
    upload_id: str,
    *,
    xml_only_if_available: bool = True,
) -> dict:
    """Extrai PDF, importa XML; IA só quando não há XML (se xml_only_if_available)."""
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

    xml_result = import_lattes_xml_if_available(session, upload_id)
    xml_sections_marked = 0
    xml_only_mode = bool(xml_result.get("xml_importado") and xml_only_if_available)
    if xml_result.get("xml_importado"):
        xml_sections_marked = mark_xml_covered_sections_extracted(session, upload_id)
        if xml_only_mode:
            xml_sections_marked = mark_all_sections_extracted(session, upload_id)

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
    for key in (
        "perfis_extraidos",
        "formacoes_extraidas",
        "producoes_extraidas",
        "projetos_extraidos",
        "financiamentos_extraidos",
    ):
        if key in xml_result:
            ai_metrics[key] += int(xml_result.get(key) or 0)

    workers = max(1, min(settings.AI_PARALLEL_WORKERS, 8))
    section_ids: list[str] = []
    if not xml_only_mode:
        if xml_result.get("xml_importado"):
            sections = list(
                session.exec(
                    select(PdfSection).where(PdfSection.curriculo_upload_id == upload_id)
                ).all()
            )
        section_ids = [s.id for s in sections if not s.status_extracao]

    if section_ids and (workers == 1 or len(section_ids) == 1):
        for section_id in section_ids:
            _, metrics, err = _extract_section_worker(section_id)
            if metrics:
                for key in ai_metrics:
                    ai_metrics[key] += metrics.get(key, 0)
            elif err:
                logger.error("Falha seção %s: %s", section_id, err)
    elif section_ids:
        logger.info(
            "Extraindo %d seções com %d workers paralelos", len(section_ids), workers
        )
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(_extract_section_worker, sid): sid for sid in section_ids
            }
            for fut in as_completed(futures):
                _, metrics, err = fut.result()
                if metrics:
                    for key in ai_metrics:
                        ai_metrics[key] += metrics.get(key, 0)
                elif err:
                    logger.error("Falha seção: %s", err)

    reconcile_result = None
    if xml_result.get("xml_importado"):
        reconcile_result = reconcile_upload_xml_pdf(session, upload_id).to_dict()

    qualis_stats = apply_qualis_to_producoes(session)

    refresh_upload_validation_status(session, upload_id)
    session.refresh(upload)
    invalidate_indicator_caches()

    return {
        "status": "sucesso",
        "upload_status": upload.status.value if hasattr(upload.status, "value") else str(upload.status),
        "secoes_detectadas": len(sections),
        "extração_ia": ai_metrics,
        "importacao_xml": xml_result,
        "secoes_xml_sem_ia": xml_sections_marked,
        "modo_somente_xml": xml_only_mode,
        "workers": workers,
        "reconciliacao": reconcile_result,
        "qualis": qualis_stats,
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
