from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json

from app.database import get_session
from app.models.core import User
from app.models.data import Projeto, Evento, Producao, Financiamento, LogValidacao
from app.models.enums import StatusValidacao

router = APIRouter(prefix="/validacao", tags=["Validation & Human-in-the-Loop"])

ENTIDADES_MAP = {
    "projetos": Projeto,
    "eventos": Evento,
    "producoes": Producao,
    "financiamentos": Financiamento
}

def get_default_user_id(session: Session) -> str:
    """Helper to ensure a user exists for logging validation actions (satisfies foreign key)."""
    user = session.exec(select(User)).first()
    if not user:
        user = User(
            id="admin_uuid_placeholder",
            name="Coordenador PPGCOM",
            email="coordenacao@ppgcom.edu",
            password_hash="mock_hash",
            role="administrador"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user.id

@router.get("/pendentes", response_model=Dict[str, List[Any]])
async def listar_pendentes(
    curriculo_upload_id: Optional[str] = None,
    professor_id: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Lists all pending items awaiting human validation (projects, events, publications, funding)."""
    results = {}
    for key, model in ENTIDADES_MAP.items():
        statement = select(model).where(model.status_validacao == StatusValidacao.PENDENTE)
        if curriculo_upload_id and hasattr(model, "curriculo_upload_id"):
            statement = statement.where(model.curriculo_upload_id == curriculo_upload_id)
        if professor_id:
            statement = statement.where(model.professor_id == professor_id)
        
        results[key] = session.exec(statement).all()
        
    return results

@router.post("/{entidade}/{id}/confirmar")
async def confirmar_registro(
    entidade: str,
    id: str,
    session: Session = Depends(get_session)
):
    """Confirms an AI-extracted record without modifications."""
    if entidade not in ENTIDADES_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Entidade '{entidade}' inválida. Use uma de: {list(ENTIDADES_MAP.keys())}"
        )
        
    model = ENTIDADES_MAP[entidade]
    obj = session.get(model, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro ID {id} não encontrado na entidade '{entidade}'."
        )
        
    obj.status_validacao = StatusValidacao.CONFIRMADO
    session.add(obj)
    
    # Log the action
    user_id = get_default_user_id(session)
    log = LogValidacao(
        user_id=user_id,
        entidade=entidade,
        entidade_id=id,
        acao="confirmar"
    )
    session.add(log)
    session.commit()
    
    return {"status": "sucesso", "mensagem": f"Registro {id} confirmado com sucesso."}

@router.post("/{entidade}/{id}/editar")
async def editar_e_confirmar_registro(
    entidade: str,
    id: str,
    updates: Dict[str, Any],
    session: Session = Depends(get_session)
):
    """Applies human corrections to a record and marks it as edited/validated."""
    if entidade not in ENTIDADES_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Entidade '{entidade}' inválida. Use uma de: {list(ENTIDADES_MAP.keys())}"
        )
        
    model = ENTIDADES_MAP[entidade]
    obj = session.get(model, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro ID {id} não encontrado na entidade '{entidade}'."
        )
        
    # Serialize old state for logging audit
    old_val_dict = obj.model_dump(exclude={"created_at", "updated_at"})
    for k, v in old_val_dict.items():
        if isinstance(v, (date, datetime)):
            old_val_dict[k] = v.isoformat()
    old_value_str = json.dumps(old_val_dict)
    
    # Apply updates
    for field, value in updates.items():
        if hasattr(obj, field):
            # Special date/datetime parsing if sent as string
            # Handle standard field coercion
            setattr(obj, field, value)
            
    obj.status_validacao = StatusValidacao.EDITADO
    session.add(obj)
    
    # Serialize new state for logging audit
    new_val_dict = obj.model_dump(exclude={"created_at", "updated_at"})
    for k, v in new_val_dict.items():
        if isinstance(v, (date, datetime)):
            new_val_dict[k] = v.isoformat()
    new_value_str = json.dumps(new_val_dict)
    
    # Log the action
    user_id = get_default_user_id(session)
    log = LogValidacao(
        user_id=user_id,
        entidade=entidade,
        entidade_id=id,
        acao="editar",
        valor_anterior=old_value_str,
        valor_novo=new_value_str
    )
    session.add(log)
    session.commit()
    session.refresh(obj)
    
    return {
        "status": "sucesso",
        "mensagem": f"Registro {id} editado e validado com sucesso.",
        "registro": obj
    }

@router.post("/{entidade}/{id}/descartar")
async def descartar_registro(
    entidade: str,
    id: str,
    session: Session = Depends(get_session)
):
    """Discards a record (soft rejection)."""
    if entidade not in ENTIDADES_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Entidade '{entidade}' inválida. Use uma de: {list(ENTIDADES_MAP.keys())}"
        )
        
    model = ENTIDADES_MAP[entidade]
    obj = session.get(model, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro ID {id} não encontrado na entidade '{entidade}'."
        )
        
    obj.status_validacao = StatusValidacao.DESCARTADO
    session.add(obj)
    
    # Log the action
    user_id = get_default_user_id(session)
    log = LogValidacao(
        user_id=user_id,
        entidade=entidade,
        entidade_id=id,
        acao="descartar"
    )
    session.add(log)
    session.commit()
    
    return {"status": "sucesso", "mensagem": f"Registro {id} descartado com sucesso."}
