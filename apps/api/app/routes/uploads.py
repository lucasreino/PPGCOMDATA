from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form, status
from sqlmodel import Session, select
import os
import shutil
import uuid
from typing import List, Optional
from app.database import get_session
from app.config import settings
from app.models.data import CurriculoUpload
from app.models.enums import StatusProcessamento
from app.services.upload_pipeline import run_full_pipeline, run_full_pipeline_background
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

@router.get("/{upload_id}", response_model=CurriculoUpload)
async def obter_upload(
    upload_id: str,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Retorna status e metadados do upload (para polling no frontend)."""
    upload = session.get(CurriculoUpload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload não encontrado.")
    return upload


@router.post("/{upload_id}/processar")
async def processar_upload(
    upload_id: str,
    background_tasks: BackgroundTasks,
    background: bool = True,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Inicia extração + IA. Por padrão roda em background e retorna imediatamente."""
    upload = session.get(CurriculoUpload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload não encontrado.")

    if upload.status == StatusProcessamento.PROCESSANDO:
        return {
            "status": "processando",
            "upload_id": upload_id,
            "mensagem": "Processamento já em andamento.",
        }

    if background:
        upload.status = StatusProcessamento.PROCESSANDO
        upload.mensagem_erro = None
        session.add(upload)
        session.commit()
        background_tasks.add_task(run_full_pipeline_background, upload_id)
        return {
            "status": "processando",
            "upload_id": upload_id,
            "mensagem": "Processamento iniciado. Acompanhe o status pelo polling.",
        }

    try:
        return run_full_pipeline(session, upload_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha no processamento: {str(e)}",
        )


@router.get("/professor/{professor_id}/latest")
async def ultimo_upload_professor(
    professor_id: str,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Retorna o upload de currículo mais recente do docente."""
    upload = session.exec(
        select(CurriculoUpload)
        .where(CurriculoUpload.professor_id == professor_id)
        .order_by(CurriculoUpload.data_upload.desc())
    ).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Nenhum currículo enviado para este docente.")
    return upload


@router.post("/professor/{professor_id}/reprocessar")
async def reprocessar_ultimo_curriculo(
    professor_id: str,
    background_tasks: BackgroundTasks,
    background: bool = True,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Reprocessa o PDF Lattes mais recente do docente (background por padrão)."""
    upload = session.exec(
        select(CurriculoUpload)
        .where(CurriculoUpload.professor_id == professor_id)
        .order_by(CurriculoUpload.data_upload.desc())
    ).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Nenhum currículo para reprocessar.")

    if upload.status == StatusProcessamento.PROCESSANDO:
        return {
            "status": "processando",
            "upload_id": upload.id,
            "mensagem": "Reprocessamento já em andamento.",
        }

    if background:
        upload.status = StatusProcessamento.PROCESSANDO
        upload.mensagem_erro = None
        session.add(upload)
        session.commit()
        background_tasks.add_task(run_full_pipeline_background, upload.id)
        return {
            "status": "processando",
            "upload_id": upload.id,
            "mensagem": "Reprocessamento iniciado em background.",
        }

    try:
        return run_full_pipeline(session, upload.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha no reprocessamento: {str(e)}",
        )
