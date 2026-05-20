from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List
from app.database import get_session
from app.models.core import Professor
from app.auth import require_staff, get_current_user
from app.schemas.professor import ProfessorListItem

router = APIRouter(prefix="/professores", tags=["Professores"])


@router.get("/", response_model=List[ProfessorListItem])
async def list_professores(
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
):
    """List all professors with research line loaded."""
    statement = select(Professor).options(selectinload(Professor.linha_pesquisa))
    results = session.exec(statement).all()
    return [ProfessorListItem.from_model(p) for p in results]


@router.post("/", response_model=Professor, status_code=status.HTTP_201_CREATED)
async def create_professor(
    professor: Professor,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Register a new professor in the system."""
    session.add(professor)
    session.commit()
    session.refresh(professor)
    return professor


@router.get("/{prof_id}", response_model=Professor)
async def get_professor(
    prof_id: str,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
):
    """Get detailed profile of a specific professor by ID."""
    professor = session.get(Professor, prof_id)
    if not professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor não encontrado",
        )
    return professor


@router.put("/{prof_id}", response_model=Professor)
async def update_professor(
    prof_id: str,
    updated_data: Professor,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Update general details of a professor's registry."""
    db_professor = session.get(Professor, prof_id)
    if not db_professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor não encontrado",
        )

    professor_data = updated_data.model_dump(exclude_unset=True)
    for key, value in professor_data.items():
        if key != "id":
            setattr(db_professor, key, value)

    session.add(db_professor)
    session.commit()
    session.refresh(db_professor)
    return db_professor
