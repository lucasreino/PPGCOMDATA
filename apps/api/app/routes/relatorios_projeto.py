from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth import require_staff
from app.database import get_session
from app.models.data import RelatorioProjeto
from app.schemas.relatorio_projeto import RelatorioProjetoCreate, RelatorioProjetoUpdate

router = APIRouter(prefix="/relatorios-projeto", tags=["Relatórios de Projeto / Extensão"])


@router.get("/", response_model=List[RelatorioProjeto])
async def listar_relatorios(
    professor_id: Optional[str] = None,
    linha_pesquisa_id: Optional[str] = None,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    stmt = select(RelatorioProjeto)
    if professor_id:
        stmt = stmt.where(RelatorioProjeto.professor_id == professor_id)
    if linha_pesquisa_id:
        stmt = stmt.where(RelatorioProjeto.linha_pesquisa_id == linha_pesquisa_id)
    return list(session.exec(stmt).all())


@router.post("/", response_model=RelatorioProjeto, status_code=status.HTTP_201_CREATED)
async def criar_relatorio(
    payload: RelatorioProjetoCreate,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    rel = RelatorioProjeto(**payload.model_dump())
    session.add(rel)
    session.commit()
    session.refresh(rel)
    return rel


@router.put("/{relatorio_id}", response_model=RelatorioProjeto)
async def atualizar_relatorio(
    relatorio_id: str,
    payload: RelatorioProjetoUpdate,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    rel = session.get(RelatorioProjeto, relatorio_id)
    if not rel:
        raise HTTPException(404, "Relatório não encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(rel, k, v)
    rel.updated_at = datetime.utcnow()
    session.add(rel)
    session.commit()
    session.refresh(rel)
    return rel


@router.delete("/{relatorio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_relatorio(
    relatorio_id: str,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    rel = session.get(RelatorioProjeto, relatorio_id)
    if not rel:
        raise HTTPException(404, "Relatório não encontrado")
    session.delete(rel)
    session.commit()
