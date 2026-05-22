from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json

from app.database import get_session
from app.models.core import User
from app.models.data import (
    Projeto,
    Evento,
    Producao,
    Financiamento,
    LogValidacao,
    AlertaLacuna,
    FormacaoAcademica,
    Orientacao,
    Banca,
    PerfilLattes,
    ProducaoTecnica,
    PremioTitulo,
    GrupoPesquisaDocente,
)
from app.models.enums import StatusValidacao
from app.auth import require_staff, get_current_user
from app.services.cache_invalidation import invalidate_indicator_caches
from app.services.upload_status import refresh_upload_validation_status

router = APIRouter(prefix="/validacao", tags=["Validation & Human-in-the-Loop"])

ENTIDADES_MAP = {
    "projetos": Projeto,
    "eventos": Evento,
    "producoes": Producao,
    "financiamentos": Financiamento,
    "formacoes_academicas": FormacaoAcademica,
    "orientacoes": Orientacao,
    "bancas": Banca,
    "perfis_lattes": PerfilLattes,
    "producoes_tecnicas": ProducaoTecnica,
    "premios": PremioTitulo,
    "grupos_pesquisa": GrupoPesquisaDocente,
}


def _maybe_refresh_upload_status(session: Session, obj) -> None:
    upload_id = getattr(obj, "curriculo_upload_id", None)
    if upload_id:
        refresh_upload_validation_status(session, upload_id)


@router.get("/pendentes", response_model=Dict[str, List[Any]])
async def listar_pendentes(
    curriculo_upload_id: Optional[str] = None,
    professor_id: Optional[str] = None,
    session: Session = Depends(get_session),
    _user: User = Depends(require_staff),
):
    """Lists all pending items awaiting human validation (projects, events, publications, funding, gaps)."""
    results = {}
    for key, model in ENTIDADES_MAP.items():
        statement = select(model).where(model.status_validacao == StatusValidacao.PENDENTE)
        if curriculo_upload_id and hasattr(model, "curriculo_upload_id"):
            statement = statement.where(model.curriculo_upload_id == curriculo_upload_id)
        if professor_id:
            statement = statement.where(model.professor_id == professor_id)

        results[key] = session.exec(statement).all()

    statement_lacunas = select(AlertaLacuna).where(AlertaLacuna.resolvido == False)
    if curriculo_upload_id:
        statement_lacunas = statement_lacunas.where(
            AlertaLacuna.curriculo_upload_id == curriculo_upload_id
        )
    if professor_id:
        statement_lacunas = statement_lacunas.where(AlertaLacuna.professor_id == professor_id)

    results["lacunas"] = session.exec(statement_lacunas).all()

    return results


@router.post("/lacunas/{id}/resolver")
async def resolver_lacuna(
    id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_staff),
):
    """Marks an information gap alert as resolved."""
    obj = session.get(AlertaLacuna, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lacuna ID {id} não encontrada.",
        )
    obj.resolvido = True
    session.add(obj)
    session.commit()
    _maybe_refresh_upload_status(session, obj)
    return {"status": "sucesso", "mensagem": f"Lacuna {id} marcada como resolvida."}


@router.post("/{entidade}/{id}/confirmar")
async def confirmar_registro(
    entidade: str,
    id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_staff),
):
    """Confirms an AI-extracted record without modifications."""
    if entidade not in ENTIDADES_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Entidade '{entidade}' inválida. Use uma de: {list(ENTIDADES_MAP.keys())}",
        )

    model = ENTIDADES_MAP[entidade]
    obj = session.get(model, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro ID {id} não encontrado na entidade '{entidade}'.",
        )

    obj.status_validacao = StatusValidacao.CONFIRMADO
    session.add(obj)

    log = LogValidacao(
        user_id=str(current_user.id),
        entidade=entidade,
        entidade_id=id,
        acao="confirmar",
    )
    session.add(log)
    session.commit()
    _maybe_refresh_upload_status(session, obj)
    invalidate_indicator_caches()

    return {"status": "sucesso", "mensagem": f"Registro {id} confirmado com sucesso."}


@router.post("/{entidade}/{id}/editar")
async def editar_e_confirmar_registro(
    entidade: str,
    id: str,
    updates: Dict[str, Any],
    session: Session = Depends(get_session),
    current_user: User = Depends(require_staff),
):
    """Applies human corrections to a record and marks it as edited/validated."""
    if entidade not in ENTIDADES_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Entidade '{entidade}' inválida. Use uma de: {list(ENTIDADES_MAP.keys())}",
        )

    model = ENTIDADES_MAP[entidade]
    obj = session.get(model, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro ID {id} não encontrado na entidade '{entidade}'.",
        )

    old_val_dict = obj.model_dump(exclude={"created_at", "updated_at"})
    for k, v in old_val_dict.items():
        if isinstance(v, (date, datetime)):
            old_val_dict[k] = v.isoformat()
    old_value_str = json.dumps(old_val_dict)

    for field, value in updates.items():
        if hasattr(obj, field):
            setattr(obj, field, value)

    obj.status_validacao = StatusValidacao.EDITADO
    session.add(obj)

    new_val_dict = obj.model_dump(exclude={"created_at", "updated_at"})
    for k, v in new_val_dict.items():
        if isinstance(v, (date, datetime)):
            new_val_dict[k] = v.isoformat()
    new_value_str = json.dumps(new_val_dict)

    log = LogValidacao(
        user_id=str(current_user.id),
        entidade=entidade,
        entidade_id=id,
        acao="editar",
        valor_anterior=old_value_str,
        valor_novo=new_value_str,
    )
    session.add(log)
    session.commit()
    session.refresh(obj)
    _maybe_refresh_upload_status(session, obj)
    invalidate_indicator_caches()

    return {
        "status": "sucesso",
        "mensagem": f"Registro {id} editado e validado com sucesso.",
        "registro": obj,
    }


@router.post("/{entidade}/{id}/descartar")
async def descartar_registro(
    entidade: str,
    id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_staff),
):
    """Discards a record (soft rejection)."""
    if entidade not in ENTIDADES_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Entidade '{entidade}' inválida. Use uma de: {list(ENTIDADES_MAP.keys())}",
        )

    model = ENTIDADES_MAP[entidade]
    obj = session.get(model, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registro ID {id} não encontrado na entidade '{entidade}'.",
        )

    obj.status_validacao = StatusValidacao.DESCARTADO
    session.add(obj)

    log = LogValidacao(
        user_id=str(current_user.id),
        entidade=entidade,
        entidade_id=id,
        acao="descartar",
    )
    session.add(log)
    session.commit()
    _maybe_refresh_upload_status(session, obj)
    invalidate_indicator_caches()

    return {"status": "sucesso", "mensagem": f"Registro {id} descartado com sucesso."}
