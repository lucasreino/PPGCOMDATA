from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.database import get_session
from app.models.core import LinhaPesquisa

router = APIRouter(prefix="/linhas-pesquisa", tags=["Linhas de Pesquisa"])

@router.get("/", response_model=List[LinhaPesquisa])
async def list_linhas(
    session: Session = Depends(get_session)
):
    """List all research lines."""
    statement = select(LinhaPesquisa)
    results = session.exec(statement).all()
    return results

@router.post("/", response_model=LinhaPesquisa, status_code=status.HTTP_201_CREATED)
async def create_linha(
    linha: LinhaPesquisa,
    session: Session = Depends(get_session)
):
    """Create a new research line."""
    session.add(linha)
    session.commit()
    session.refresh(linha)
    return linha

@router.get("/{linha_id}", response_model=LinhaPesquisa)
async def get_linha(
    linha_id: str,
    session: Session = Depends(get_session)
):
    """Get a single research line by ID."""
    linha = session.get(LinhaPesquisa, linha_id)
    if not linha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linha de pesquisa não encontrada"
        )
    return linha

@router.put("/{linha_id}", response_model=LinhaPesquisa)
async def update_linha(
    linha_id: str,
    updated_data: LinhaPesquisa,
    session: Session = Depends(get_session)
):
    """Update an existing research line."""
    db_linha = session.get(LinhaPesquisa, linha_id)
    if not db_linha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linha de pesquisa não encontrada"
        )
    
    # Update fields
    linha_data = updated_data.dict(exclude_unset=True)
    for key, value in linha_data.items():
        if key != "id":
            setattr(db_linha, key, value)
            
    session.add(db_linha)
    session.commit()
    session.refresh(db_linha)
    return db_linha
