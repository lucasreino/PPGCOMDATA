from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form, status
from sqlmodel import Session, select
from typing import Literal, Optional

from app.database import get_session
from app.models.data import CurriculoUpload
from app.models.enums import StatusProcessamento
from app.services.lattes_curriculo_import import (
    run_lattes_xml_import_pipeline,
    resolve_xml_path_for_upload_record,
    save_and_import_lattes_file,
)
from app.auth import require_staff

router = APIRouter(prefix="/uploads", tags=["Uploads & Processing"])


@router.post("/lattes")
async def upload_lattes_curriculo(
    professor_id: str = Form(...),
    fonte: Literal["html", "xml"] = Form(...),
    ano_inicio: Optional[int] = Form(None),
    ano_fim: Optional[int] = Form(None),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """
    Importa currículo Lattes a partir de:
    - **html**: página HTML salva do Lattes (convertida para XML via lattes-xml)
    - **xml**: arquivo XML exportado diretamente
    """
    try:
        return save_and_import_lattes_file(
            session,
            professor_id,
            file,
            fonte,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na importação do currículo: {exc}",
        ) from exc


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
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Reimporta o XML do upload (HTML já convertido ou XML enviado)."""
    upload = session.get(CurriculoUpload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload não encontrado.")

    xml_path = resolve_xml_path_for_upload_record(upload)
    if not xml_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não há XML disponível para este upload. Envie HTML ou XML novamente.",
        )

    if upload.status == StatusProcessamento.PROCESSANDO:
        return {
            "status": "processando",
            "upload_id": upload_id,
            "mensagem": "Processamento já em andamento.",
        }

    try:
        return run_lattes_xml_import_pipeline(session, upload_id, xml_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha no processamento: {exc}",
        ) from exc


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
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Reimporta o último currículo Lattes (XML/HTML) do docente."""
    upload = session.exec(
        select(CurriculoUpload)
        .where(CurriculoUpload.professor_id == professor_id)
        .order_by(CurriculoUpload.data_upload.desc())
    ).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Nenhum currículo para reprocessar.")

    xml_path = resolve_xml_path_for_upload_record(upload)
    if not xml_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Último envio não possui XML reutilizável. Importe HTML ou XML novamente.",
        )

    if upload.status == StatusProcessamento.PROCESSANDO:
        return {
            "status": "processando",
            "upload_id": upload.id,
            "mensagem": "Reprocessamento já em andamento.",
        }

    try:
        return run_lattes_xml_import_pipeline(session, str(upload.id), xml_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha no reprocessamento: {exc}",
        ) from exc
