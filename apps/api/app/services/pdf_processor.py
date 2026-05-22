import fitz  # PyMuPDF
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlmodel import Session
from app.models.data import CurriculoUpload, PdfPage
from app.models.enums import StatusProcessamento
from app.services.text_preprocessor import normalize_lattes_text

logger = logging.getLogger("ppgcomdata.pdf_processor")


def extract_text_by_page(file_path: str) -> List[Dict[str, Any]]:
    """Extrai texto página a página com PyMuPDF (modo ordenado + fallback)."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo PDF não encontrado no caminho: {file_path}")

    pages_data: List[Dict[str, Any]] = []
    doc = fitz.open(file_path)
    try:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text", sort=True) or ""
            if len(text.strip()) < 40:
                text = page.get_text() or ""
            text = text.replace("\x00", "")
            pages_data.append({
                "numero_pagina": page_num + 1,
                "texto": text,
            })
    finally:
        doc.close()

    return pages_data


def extract_full_text(pages_data: List[Dict[str, Any]]) -> str:
    """Concatena páginas com marcadores corretos e normaliza o texto."""
    parts: List[str] = []
    for page in pages_data:
        parts.append(f"\n\n--- PAGINA {page['numero_pagina']} ---\n\n")
        parts.append(page["texto"])
    return normalize_lattes_text("".join(parts))


def detect_pdf_quality(pages_data: List[Dict[str, Any]]) -> Tuple[bool, int]:
    """Avalia se o PDF tem texto extraível suficiente (não só imagem)."""
    total_chars = sum(len(page["texto"].strip()) for page in pages_data)
    is_good = total_chars >= 1000
    return is_good, total_chars


def save_pages_to_database(
    session: Session,
    curriculo_upload_id: str,
    professor_id: str,
    pages_data: List[Dict[str, Any]],
) -> None:
    """Salva cada página extraída na tabela pdf_pages."""
    pages = [
        PdfPage(
            curriculo_upload_id=curriculo_upload_id,
            professor_id=professor_id,
            numero_pagina=page["numero_pagina"],
            texto=page["texto"],
        )
        for page in pages_data
    ]
    session.add_all(pages)
    session.commit()


def process_curriculo_pdf(session: Session, curriculo_upload_id: str) -> CurriculoUpload:
    """Orquestra extração de texto do PDF Lattes."""
    upload = session.get(CurriculoUpload, curriculo_upload_id)
    if not upload:
        raise ValueError(f"Upload ID {curriculo_upload_id} não encontrado no banco.")

    upload.status = StatusProcessamento.PROCESSANDO
    upload.data_processamento = datetime.utcnow()
    session.add(upload)
    session.commit()
    session.refresh(upload)

    logger.info("Iniciando processamento do curriculo ID: %s", curriculo_upload_id)

    try:
        file_path = upload.arquivo_url
        pages_data = extract_text_by_page(file_path)

        is_valid_quality, total_chars = detect_pdf_quality(pages_data)
        if not is_valid_quality:
            upload.status = StatusProcessamento.ERRO_NO_PROCESSAMENTO
            upload.mensagem_erro = (
                f"PDF com baixo teor de texto ({total_chars} caracteres). Possivelmente escaneado."
            )
            session.add(upload)
            session.commit()
            logger.warning(
                "Processamento falhou por baixa qualidade do PDF ID: %s", curriculo_upload_id
            )
            return upload

        full_text = extract_full_text(pages_data)
        upload.texto_extraido = full_text
        upload.status = StatusProcessamento.PROCESSADO_COM_SUCESSO
        session.add(upload)
        session.commit()

        save_pages_to_database(session, curriculo_upload_id, upload.professor_id, pages_data)

        logger.info("Texto do PDF ID %s extraido e armazenado com sucesso.", curriculo_upload_id)
        session.refresh(upload)
        return upload

    except Exception as e:
        logger.error(
            "Erro inesperado no processamento do PDF ID %s: %s", curriculo_upload_id, str(e)
        )
        upload.status = StatusProcessamento.ERRO_NO_PROCESSAMENTO
        upload.mensagem_erro = f"Falha no processamento: {str(e)}"
        session.add(upload)
        session.commit()
        session.refresh(upload)
        return upload
