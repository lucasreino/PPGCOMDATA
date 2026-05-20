from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List
from app.database import get_session
from app.models.core import Professor
from app.models.data import Orientacao, FormacaoAcademica, Banca
from app.models.enums import StatusOrientacao
from app.auth import require_staff, get_current_user
from app.schemas.professor import ProfessorListItem
from app.schemas.professor_resumo import (
    ProfessorResumoAcademico,
    OrientacaoResumoItem,
    FormacaoResumoItem,
)
from app.services.professor_lookup import find_professor, professor_dedupe_key

router = APIRouter(prefix="/professores", tags=["Professores"])


@router.get("/", response_model=List[ProfessorListItem])
async def list_professores(
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
):
    """List all professors with research line loaded."""
    statement = select(Professor).options(selectinload(Professor.linha_pesquisa))
    results = session.exec(statement).all()

    seen: set[str] = set()
    unique: list[Professor] = []
    for prof in sorted(results, key=lambda p: p.nome_completo or ""):
        key = professor_dedupe_key(prof)
        if key in seen:
            continue
        seen.add(key)
        unique.append(prof)

    return [ProfessorListItem.from_model(p) for p in unique]


@router.post("/", response_model=Professor, status_code=status.HTTP_201_CREATED)
async def create_professor(
    professor: Professor,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Register a new professor in the system."""
    existing = find_professor(
        session,
        nome_completo=professor.nome_completo,
        email=professor.email,
        id_lattes=professor.id_lattes,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Docente já cadastrado: {existing.nome_completo}",
        )
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


@router.get("/{prof_id}/resumo-academico", response_model=ProfessorResumoAcademico)
async def get_resumo_academico(
    prof_id: str,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
):
    """Indicadores de formação, orientações e bancas extraídos dos PDFs Lattes."""
    professor = session.get(Professor, prof_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")

    orientacoes = session.exec(
        select(Orientacao).where(Orientacao.professor_id == prof_id)
    ).all()
    formacoes = session.exec(
        select(FormacaoAcademica).where(FormacaoAcademica.professor_id == prof_id)
    ).all()
    bancas = session.exec(select(Banca).where(Banca.professor_id == prof_id)).all()

    current_year = date.today().year
    cutoff = current_year - 5
    concluidas = [o for o in orientacoes if o.status == StatusOrientacao.CONCLUIDA]
    em_andamento = [o for o in orientacoes if o.status == StatusOrientacao.EM_ANDAMENTO]
    ultimos_5 = [
        o
        for o in orientacoes
        if (o.ano_conclusao and o.ano_conclusao >= cutoff)
        or (o.ano_inicio and o.ano_inicio >= cutoff)
    ]

    return ProfessorResumoAcademico(
        professor_id=str(professor.id),
        titulacao_maxima=professor.titulacao_maxima,
        data_ultima_atualizacao_lattes=(
            professor.data_ultima_atualizacao_lattes.isoformat()
            if professor.data_ultima_atualizacao_lattes
            else None
        ),
        total_orientacoes=len(orientacoes),
        orientacoes_concluidas=len(concluidas),
        orientacoes_em_andamento=len(em_andamento),
        orientacoes_ultimos_5_anos=len(ultimos_5),
        total_bancas=len(bancas),
        total_formacoes=len(formacoes),
        orientacoes=[
            OrientacaoResumoItem(
                id=str(o.id),
                tipo=o.tipo.value,
                status=o.status.value,
                nome_orientando=o.nome_orientando,
                titulo_trabalho=o.titulo_trabalho,
                ano_conclusao=o.ano_conclusao,
                status_validacao=o.status_validacao.value,
            )
            for o in orientacoes[:50]
        ],
        formacoes=[
            FormacaoResumoItem(
                id=str(f.id),
                nivel=f.nivel.value,
                curso=f.curso,
                instituicao=f.instituicao,
                ano_fim=f.ano_fim,
                status_validacao=f.status_validacao.value,
            )
            for f in formacoes
        ],
    )


@router.get("/{prof_id}/orientacoes", response_model=List[Orientacao])
async def list_orientacoes(
    prof_id: str,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
):
    professor = session.get(Professor, prof_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    return session.exec(select(Orientacao).where(Orientacao.professor_id == prof_id)).all()


@router.get("/{prof_id}/formacoes", response_model=List[FormacaoAcademica])
async def list_formacoes(
    prof_id: str,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
):
    professor = session.get(Professor, prof_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    return session.exec(
        select(FormacaoAcademica).where(FormacaoAcademica.professor_id == prof_id)
    ).all()


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
