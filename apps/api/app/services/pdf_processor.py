import fitz  # PyMuPDF
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlmodel import Session
from app.models.data import CurriculoUpload, PdfPage
from app.models.enums import StatusProcessamento

logger = logging.getLogger("ppgcomdata.pdf_processor")

def extract_text_by_page(file_path: str) -> List[Dict[str, Any]]:
    """Extracts text page by page from a PDF file using PyMuPDF.
    
    Returns:
        List of dicts containing:
        - "numero_pagina": 1-based page index
        - "texto": extracted text string
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo PDF não encontrado no caminho: {file_path}")
        
    pages_data = []
    
    # Open PDF document
    doc = fitz.open(file_path)
    try:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            pages_data.append({
                "numero_pagina": page_num + 1,
                "texto": text or ""
            })
    finally:
        doc.close()
        
    return pages_data

def extract_full_text(pages_data: List[Dict[str, Any]]) -> str:
    """Concatenates pages text into a single cohesive string."""
    return "\n\n--- PAGINA %d ---\n\n" % 1 + "\n".join([page["texto"] for page in pages_data])

def detect_pdf_quality(pages_data: List[Dict[str, Any]]) -> Tuple[bool, int]:
    """Evaluates whether the PDF has enough extractable text or is likely a scanned image.
    
    Returns:
        Tuple[is_good_quality: bool, total_characters: int]
    """
    total_chars = sum(len(page["texto"].strip()) for page in pages_data)
    # If a multi-page PDF has less than 1000 characters, it is likely scanned
    is_good = total_chars >= 1000
    return is_good, total_chars

def save_pages_to_database(
    session: Session, 
    curriculo_upload_id: str, 
    professor_id: str, 
    pages_data: List[Dict[str, Any]]
) -> None:
    """Saves each extracted PDF page into the pdf_pages table."""
    for page in pages_data:
        db_page = PdfPage(
            curriculo_upload_id=curriculo_upload_id,
            professor_id=professor_id,
            numero_pagina=page["numero_pagina"],
            texto=page["texto"]
        )
        session.add(db_page)
    session.commit()

def process_curriculo_pdf(session: Session, curriculo_upload_id: str) -> CurriculoUpload:
    """Orchestrates the entire PDF text extraction pipeline.
    
    Loads upload, reads PDF, validates character metrics, and stores text outputs.
    """
    upload = session.get(CurriculoUpload, curriculo_upload_id)
    if not upload:
        raise ValueError(f"Upload ID {curriculo_upload_id} não encontrado no banco.")
        
    # Update status to processing
    upload.status = StatusProcessamento.PROCESSANDO
    upload.data_processamento = datetime.utcnow()
    session.add(upload)
    session.commit()
    session.refresh(upload)
    
    logger.info(f"Iniciando processamento do curriculo ID: {curriculo_upload_id}")
    
    try:
        # 1. Extract text page-by-page
        # In a real environment, upload.arquivo_url points to a local file or remote bucket.
        # We assume local file path for development.
        file_path = upload.arquivo_url
        pages_data = extract_text_by_page(file_path)
        
        # 2. Check quality
        is_valid_quality, total_chars = detect_pdf_quality(pages_data)
        if not is_valid_quality:
            upload.status = StatusProcessamento.ERRO_NO_PROCESSAMENTO
            upload.mensagem_erro = f"PDF com baixo teor de texto ({total_chars} caracteres). Possivelmente escaneado."
            session.add(upload)
            session.commit()
            logger.warning(f"Processamento falhou por baixa qualidade do PDF ID: {curriculo_upload_id}")
            return upload
            
        # 3. Concatenate and save full text
        full_text = extract_full_text(pages_data)
        upload.texto_extraido = full_text
        upload.status = StatusProcessamento.PROCESSADO_COM_SUCESSO
        session.add(upload)
        session.commit()
        
        # 4. Save pages into database
        save_pages_to_database(session, curriculo_upload_id, upload.professor_id, pages_data)
        
        logger.info(f"Texto do PDF ID {curriculo_upload_id} extraido e armazenado com sucesso.")
        session.refresh(upload)
        return upload
        
    except Exception as e:
        logger.error(f"Erro inesperado no processamento do PDF ID {curriculo_upload_id}: {str(e)}")
        upload.status = StatusProcessamento.ERRO_NO_PROCESSAMENTO
        upload.mensagem_erro = f"Falha no processamento: {str(e)}"
        session.add(upload)
        session.commit()
        session.refresh(upload)
        return upload
