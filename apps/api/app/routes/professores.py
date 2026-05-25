from datetime import date
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload
from typing import Any, Dict, List
from app.database import get_session
from app.models.core import Professor
from app.models.data import (
    Orientacao,
    FormacaoAcademica,
    Banca,
    Projeto,
    Evento,
    Producao,
    Financiamento,
    ProducaoTecnica,
    PremioTitulo,
    GrupoPesquisaDocente,
)
from app.models.enums import StatusOrientacao, TipoDocente
from app.auth import require_staff, get_current_user
from app.schemas.professor_cadastro import ProfessorCadastroResponse
from app.services.professor_cadastro import cadastrar_professor
from app.schemas.professor import ProfessorListItem
from app.schemas.professor_catalog import ProfessorCatalogItem
from app.schemas.professor_resumo import (
    ProfessorResumoAcademico,
    OrientacaoResumoItem,
    FormacaoResumoItem,
)
from app.services.professor_lookup import find_professor, professor_dedupe_key
from app.routes.validacao import ENTIDADES_MAP
from app.services.entity_sort import sort_entities_newest_first

router = APIRouter(prefix="/professores", tags=["Professores"])

_COUNT_MODELS = {
    "total_projetos": Projeto,
    "total_eventos": Evento,
    "total_producoes": Producao,
    "total_financiamentos": Financiamento,
    "total_orientacoes": Orientacao,
    "total_bancas": Banca,
}


def _counts_by_professor(session: Session) -> Dict[str, Dict[str, int]]:
    """Contagens por professor_id para o catálogo."""
    result: Dict[str, Dict[str, int]] = {}
    for key, model in _COUNT_MODELS.items():
        rows = session.exec(
            select(model.professor_id, func.count()).group_by(model.professor_id)  # type: ignore[arg-type]
        ).all()
        for prof_id, count in rows:
            pid = str(prof_id)
            if pid not in result:
                result[pid] = {}
            result[pid][key] = int(count)
    return result


def _serialize_entities(
    rows: List[Any], *, include_trecho: bool = True
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        data = row.model_dump(mode="json")
        if not include_trecho:
            data.pop("trecho_original", None)
        out.append(data)
    return out


def _catalog_item_for_professor(
    prof: Professor, counts: Dict[str, Dict[str, int]]
) -> ProfessorCatalogItem:
    pid = str(prof.id)
    c = counts.get(pid, {})
    base = ProfessorListItem.from_model(prof)
    return ProfessorCatalogItem(
        **base.model_dump(),
        total_projetos=c.get("total_projetos", 0),
        total_producoes=c.get("total_producoes", 0),
        total_eventos=c.get("total_eventos", 0),
        total_orientacoes=c.get("total_orientacoes", 0),
        total_bancas=c.get("total_bancas", 0),
        total_financiamentos=c.get("total_financiamentos", 0),
    )


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


@router.get("/catalog", response_model=List[ProfessorCatalogItem])
async def list_professores_catalog(
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
):
    """Lista docentes com foto, linha e contagens para o grid de perfis."""
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

    counts = _counts_by_professor(session)
    return [_catalog_item_for_professor(prof, counts) for prof in unique]


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


@router.post("/cadastro", response_model=ProfessorCadastroResponse, status_code=status.HTTP_201_CREATED)
async def cadastrar_professor_completo(
    nome_completo: str = Form(...),
    email: str | None = Form(None),
    link_lattes: str | None = Form(None),
    id_lattes: str | None = Form(None),
    tipo_docente: str = Form("permanente"),
    linha_pesquisa_id: str | None = Form(None),
    grupo_pesquisa: str | None = Form(None),
    tematicas: str | None = Form(None),
    xml_curriculo: UploadFile | None = File(None),
    foto: UploadFile | None = File(None),
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    """Cadastra docente com identificação, foto e importação opcional de XML Lattes."""
    try:
        tipo = TipoDocente(tipo_docente.strip().lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tipo_docente inválido. Use: permanente, colaborador, visitante ou externo.",
        )

    try:
        payload = cadastrar_professor(
            session,
            nome_completo=nome_completo,
            email=email,
            link_lattes=link_lattes,
            id_lattes=id_lattes,
            tipo_docente=tipo,
            linha_pesquisa_id=linha_pesquisa_id,
            grupo_pesquisa=grupo_pesquisa,
            tematicas=tematicas,
            xml_file=xml_curriculo,
            foto_file=foto,
        )
    except ValueError as exc:
        msg = str(exc)
        code = status.HTTP_409_CONFLICT if "já cadastrado" in msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=msg) from exc

    mensagem = "Docente cadastrado com sucesso e incluído no cadastro oficial do PPGCOM."
    if payload.get("xml_importado"):
        mensagem += " Currículo XML importado."
    if payload.get("foto_url"):
        mensagem += " Foto salva."

    return ProfessorCadastroResponse(
        professor_id=payload["professor_id"],
        nome_completo=payload["nome_completo"],
        id_lattes=payload.get("id_lattes"),
        foto_url=payload.get("foto_url"),
        xml_importado=bool(payload.get("xml_importado")),
        upload_id=payload.get("upload_id"),
        upload_status=payload.get("upload_status"),
        metrics=payload.get("metrics"),
        cadastro_oficial=bool(payload.get("cadastro_oficial", True)),
        linha_oficial=payload.get("linha_oficial"),
        mensagem=mensagem,
    )


@router.get("/{prof_id}/catalog", response_model=ProfessorCatalogItem)
async def get_professor_catalog_item(
    prof_id: str,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
):
    """Metadados do docente + contagens (sem carregar catálogo inteiro)."""
    professor = session.get(Professor, prof_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    counts = _counts_by_professor(session)
    return _catalog_item_for_professor(professor, counts)


@router.get("/{prof_id}/dados")
async def get_professor_dados(
    prof_id: str,
    include_trecho: bool = False,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
):
    """Todos os registros do docente (qualquer status de validação)."""
    professor = session.get(Professor, prof_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")

    payload: Dict[str, Any] = {
        "professor": ProfessorListItem.from_model(professor).model_dump(),
    }
    for key, model in ENTIDADES_MAP.items():
        rows = session.exec(select(model).where(model.professor_id == prof_id)).all()
        payload[key] = _serialize_entities(
            sort_entities_newest_first(rows, key), include_trecho=include_trecho
        )

    return payload


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

    orientacoes = sort_entities_newest_first(
        session.exec(select(Orientacao).where(Orientacao.professor_id == prof_id)).all(),
        "orientacoes",
    )
    formacoes = sort_entities_newest_first(
        session.exec(
            select(FormacaoAcademica).where(FormacaoAcademica.professor_id == prof_id)
        ).all(),
        "formacoes_academicas",
    )
    bancas = sort_entities_newest_first(
        session.exec(select(Banca).where(Banca.professor_id == prof_id)).all(),
        "bancas",
    )

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
    rows = session.exec(select(Orientacao).where(Orientacao.professor_id == prof_id)).all()
    return sort_entities_newest_first(rows, "orientacoes")


@router.get("/{prof_id}/formacoes", response_model=List[FormacaoAcademica])
async def list_formacoes(
    prof_id: str,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
):
    professor = session.get(Professor, prof_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    rows = session.exec(
        select(FormacaoAcademica).where(FormacaoAcademica.professor_id == prof_id)
    ).all()
    return sort_entities_newest_first(rows, "formacoes_academicas")


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
