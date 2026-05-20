from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.database import get_session
from app.models.core import Professor

router = APIRouter(prefix="/professores", tags=["Professores"])

@router.get("/", response_model=List[Professor])
async def list_professores(
    session: Session = Depends(get_session)
):
    """List all professors in the postgraduate program."""
    statement = select(Professor)
    results = session.exec(statement).all()
    return results

@router.post("/", response_model=Professor, status_code=status.HTTP_201_CREATED)
async def create_professor(
    professor: Professor,
    session: Session = Depends(get_session)
):
    """Register a new professor in the system."""
    session.add(professor)
    session.commit()
    session.refresh(professor)
    return professor

@router.get("/{prof_id}", response_model=Professor)
async def get_professor(
    prof_id: str,
    session: Session = Depends(get_session)
):
    """Get detailed profile of a specific professor by ID."""
    professor = session.get(Professor, prof_id)
    if not professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor não encontrado"
        )
    return professor

@router.put("/{prof_id}", response_model=Professor)
async def update_professor(
    prof_id: str,
    updated_data: Professor,
    session: Session = Depends(get_session)
):
    """Update general details of a professor's registry."""
    db_professor = session.get(Professor, prof_id)
    if not db_professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor não encontrado"
        )
    
    # Update fields
    professor_data = updated_data.dict(exclude_unset=True)
    for key, value in professor_data.items():
        if key != "id":
            setattr(db_professor, key, value)
            
    session.add(db_professor)
    session.commit()
    session.refresh(db_professor)
    return db_professor
