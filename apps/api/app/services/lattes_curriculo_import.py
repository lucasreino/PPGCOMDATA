"""Importação de currículo Lattes via HTML (conversão) ou XML direto."""

from __future__ import annotations

import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import UploadFile
from sqlmodel import Session

from app.config import settings
from app.models.core import Professor
from app.models.data import CurriculoUpload
from app.models.enums import StatusProcessamento
from app.services.lattes_xml_importer import import_lattes_xml
from app.services.professor_lookup import normalize_lattes_id
from app.services.upload_cleanup import clear_upload_extraction_data, mark_all_sections_extracted
from app.services.upload_status import refresh_upload_validation_status
from app.services.qualis_catalog import apply_qualis_to_producoes
from app.services.journal_hindex_catalog import apply_journal_hindex_to_producoes
from app.services.scholar_metrics_catalog import apply_scholar_metrics_to_producoes
from app.services.cache_invalidation import invalidate_indicator_caches

# Pacote lattes-xml embutido em apps/api/vendor
_VENDOR = Path(__file__).resolve().parents[2] / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

from lattes_converter.converter import convert_html_to_xml  # noqa: E402

LattesFonte = Literal["html", "xml"]

_HTML_EXT = {".html", ".htm"}
_XML_EXT = {".xml"}


def _upload_subdir(name: str) -> Path:
    base = Path(settings.UPLOAD_DIR)
    dest = base / name
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def _ext(filename: str | None) -> str:
    return os.path.splitext(filename or "")[1].lower()


def validate_lattes_file(filename: str | None, fonte: LattesFonte) -> None:
    ext = _ext(filename)
    if fonte == "html" and ext not in _HTML_EXT:
        raise ValueError("Envie o currículo salvo do Lattes em HTML (.html ou .htm).")
    if fonte == "xml" and ext not in _XML_EXT:
        raise ValueError("Envie um arquivo XML exportado do Lattes (.xml).")


def convert_html_file_to_xml(html_path: Path, xml_path: Path) -> Path:
    """Converte HTML Lattes para XML usando o módulo lattes-xml."""
    convert_html_to_xml(html_path, xml_path)
    if not xml_path.is_file():
        raise ValueError("Falha ao gerar XML a partir do HTML.")
    return xml_path


def persist_xml_for_professor(prof: Professor, xml_path: Path) -> None:
    lid = normalize_lattes_id(prof.id_lattes)
    xml_dir = (settings.LATTES_XML_DIR or "").strip()
    if not lid or not xml_dir:
        return
    target_dir = Path(xml_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(xml_path, target_dir / f"{lid}.xml")


def resolve_xml_path_for_upload_record(upload: CurriculoUpload) -> Optional[Path]:
    """Retorna o XML associado ao upload (arquivo salvo ou pasta LATTES_XML_DIR)."""
    path = Path(upload.arquivo_url or "")
    if path.is_file() and path.suffix.lower() == ".xml":
        return path
    if path.is_file() and path.suffix.lower() in _HTML_EXT:
        generated = path.with_suffix(".xml")
        if generated.is_file():
            return generated
        return convert_html_file_to_xml(path, generated)
    return None


def run_lattes_xml_import_pipeline(
    session: Session,
    upload_id: str,
    xml_path: str | Path,
) -> dict[str, Any]:
    """Importa XML no upload, aplica Qualis e atualiza status (sem PDF/IA)."""
    path = Path(xml_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))

    upload = session.get(CurriculoUpload, upload_id)
    if not upload:
        raise ValueError(f"Upload {upload_id} não encontrado.")

    upload.status = StatusProcessamento.PROCESSANDO
    upload.mensagem_erro = None
    session.add(upload)
    session.commit()

    try:
        clear_upload_extraction_data(session, upload_id)
        metrics = import_lattes_xml(session, upload_id, path)
        mark_all_sections_extracted(session, upload_id)

        prof = session.get(Professor, upload.professor_id)
        if prof:
            if not prof.id_lattes:
                # id_lattes pode ter sido preenchido pelo import
                session.refresh(prof)
            persist_xml_for_professor(prof, path)

        qualis_stats = apply_qualis_to_producoes(session)
        scholar_stats = apply_scholar_metrics_to_producoes(session)
        journal_hindex_stats = apply_journal_hindex_to_producoes(session)
        refresh_upload_validation_status(session, upload_id)

        upload.status = StatusProcessamento.PROCESSADO_COM_SUCESSO
        session.add(upload)
        session.commit()
        session.refresh(upload)
        invalidate_indicator_caches()

        return {
            "status": "sucesso",
            "upload_id": upload_id,
            "upload_status": upload.status.value,
            "importacao_xml": {**metrics, "xml_importado": True, "xml_arquivo": path.name},
            "qualis": qualis_stats,
            "scholar_metrics": scholar_stats,
            "journal_hindex": journal_hindex_stats,
            "modo": "xml_lattes",
        }
    except Exception as exc:
        upload.status = StatusProcessamento.ERRO_NO_PROCESSAMENTO
        upload.mensagem_erro = str(exc)[:500]
        session.add(upload)
        session.commit()
        raise


def save_and_import_lattes_file(
    session: Session,
    professor_id: str,
    file: UploadFile,
    fonte: LattesFonte,
    *,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
) -> dict[str, Any]:
    """Salva HTML ou XML, converte se necessário e importa no banco."""
    validate_lattes_file(file.filename, fonte)

    prof = session.get(Professor, professor_id)
    if not prof:
        raise ValueError("Professor não encontrado.")

    original_name = file.filename or f"curriculo.{fonte}"
    stored_id = uuid.uuid4().hex

    if fonte == "html":
        html_dir = _upload_subdir("html")
        html_path = html_dir / f"{stored_id}.html"
        with open(html_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        xml_dir = _upload_subdir("xml")
        xml_path = xml_dir / f"{stored_id}.xml"
        convert_html_file_to_xml(html_path, xml_path)
        arquivo_url = str(xml_path)
        arquivo_nome = original_name
    else:
        xml_dir = _upload_subdir("xml")
        xml_path = xml_dir / f"{stored_id}.xml"
        with open(xml_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        arquivo_url = str(xml_path)
        arquivo_nome = original_name

    upload = CurriculoUpload(
        professor_id=professor_id,
        arquivo_url=arquivo_url,
        arquivo_nome=arquivo_nome,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        status=StatusProcessamento.AGUARDANDO_PROCESSAMENTO,
    )
    session.add(upload)
    session.commit()
    session.refresh(upload)

    result = run_lattes_xml_import_pipeline(session, str(upload.id), arquivo_url)
    result["fonte"] = fonte
    result["arquivo_nome"] = arquivo_nome
    return result
