from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlmodel import Session, select
import os
import shutil
import uuid
from typing import List, Optional
from app.database import get_session
from app.config import settings
from app.models.data import CurriculoUpload, PdfSection
from app.models.enums import StatusProcessamento
from app.services.pdf_processor import process_curriculo_pdf
from app.services.section_detector import split_and_save_sections
from app.services.ai_extractor import extract_and_save_section_data
from app.services.upload_status import refresh_upload_validation_status
from app.auth import require_staff

router = APIRouter(prefix="/uploads", tags=["Uploads & Processing"])

@router.post("/", response_model=CurriculoUpload, status_code=status.HTTP_201_CREATED)
async def upload_curriculo(
    professor_id: str = Form(...),
    ano_inicio: Optional[int] = Form(None),
    ano_fim: Optional[int] = Form(None),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Uploads a digital Currículo Lattes PDF and creates the upload record."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos PDF são permitidos."
        )
        
    # Generate unique filename to avoid collision
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    dest_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Save the file locally
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar arquivo no servidor: {str(e)}"
        )
        
    # Create database record
    db_upload = CurriculoUpload(
        professor_id=professor_id,
        arquivo_url=dest_path, # Store absolute path for easy server parsing
        arquivo_nome=file.filename,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        status=StatusProcessamento.AGUARDANDO_PROCESSAMENTO
    )
    
    session.add(db_upload)
    session.commit()
    session.refresh(db_upload)
    
    return db_upload

@router.post("/{upload_id}/processar")
async def processar_upload(
    upload_id: str,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Orchestrates the full extraction pipeline: text extraction, section splitting, and AI processing."""
    # 1. Page extraction & density checking
    try:
        upload = process_curriculo_pdf(session, upload_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na extração de texto do PDF: {str(e)}"
        )
        
    if upload.status == StatusProcessamento.ERRO_NO_PROCESSAMENTO:
        return {
            "status": "erro",
            "mensagem": upload.mensagem_erro
        }
        
    # 2. Section detection & partitioning
    try:
        sections = split_and_save_sections(session, upload_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao particionar seções do currículo: {str(e)}"
        )
        
    if not sections:
        upload.status = StatusProcessamento.PROCESSADO_COM_ALERTAS
        session.add(upload)
        session.commit()
        return {
            "status": "sucesso_com_alertas",
            "mensagem": "Texto extraído, mas nenhuma seção relevante do Lattes foi identificada.",
        }
        
    # 3. AI structured extraction for each section
    ai_metrics = {
        "projetos_extraidos": 0,
        "eventos_extraidos": 0,
        "producoes_extraidas": 0,
        "financiamentos_extraidos": 0,
        "lacunas_extraidas": 0
    }
    
    for section in sections:
        try:
            metrics = extract_and_save_section_data(session, section.id)
            for key in ai_metrics:
                ai_metrics[key] += metrics.get(key, 0)
        except Exception as e:
            # We log the error but continue extracting other sections
            print(f"Erro ao processar seção '{section.nome_secao}' via IA: {str(e)}")
            
    refresh_upload_validation_status(session, upload_id)
    session.refresh(upload)

    return {
        "status": "sucesso",
        "upload_status": upload.status.value,
        "secoes_detectadas": len(sections),
        "extração_ia": ai_metrics,
    }
