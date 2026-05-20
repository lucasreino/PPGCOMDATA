from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import require_staff
from app.database import get_session
from app.models.data import AlertaLacuna
from app.models.enums import StatusTratamentoLacuna, GravidadeLacuna

router = APIRouter(prefix="/lacunas", tags=["Lacunas APCN"])


class LacunaUpdate(BaseModel):
    resolvido: Optional[bool] = None
    status_tratamento: Optional[StatusTratamentoLacuna] = None
    secao_documento: Optional[str] = None
    prioridade: Optional[str] = None
    responsavel: Optional[str] = None
    prazo: Optional[date] = None
    sugestao_de_correcao: Optional[str] = None
    acao_recomendada: Optional[str] = None
    gravidade: Optional[GravidadeLacuna] = None


@router.patch("/{lacuna_id}", response_model=AlertaLacuna)
async def atualizar_lacuna(
    lacuna_id: str,
    payload: LacunaUpdate,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    lac = session.get(AlertaLacuna, lacuna_id)
    if not lac:
        raise HTTPException(404, "Lacuna não encontrada")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(lac, k, v)
    if data.get("resolvido") is True:
        lac.status_tratamento = StatusTratamentoLacuna.RESOLVIDA
    elif data.get("resolvido") is False:
        lac.status_tratamento = StatusTratamentoLacuna.ABERTA
    lac.updated_at = datetime.utcnow()
    session.add(lac)
    session.commit()
    session.refresh(lac)
    return lac
