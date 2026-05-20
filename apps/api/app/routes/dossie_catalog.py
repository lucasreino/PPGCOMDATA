"""CRUD e importação CSV para dados do Dossiê APCN (não vêm do Lattes)."""

import csv
import io
from datetime import datetime
from typing import List, Type

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session, SQLModel, select

from app.auth import require_staff
from app.database import get_session
from app.models.data import EventoInstitucional, Egresso, ProcessoSeletivo

router = APIRouter(prefix="/dossie-apcn/catalog", tags=["Dossiê APCN — Cadastros"])


def _import_csv(session: Session, model: Type[SQLModel], content: bytes, fieldnames: List[str]):
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV vazio ou sem cabeçalho.")
    created = 0
    now = datetime.utcnow()
    for row in reader:
        data = {k: (row.get(k) or "").strip() or None for k in fieldnames if k in (reader.fieldnames or [])}
        if model == Egresso and not data.get("nome"):
            continue
        if model == ProcessoSeletivo:
            if not data.get("ano") or not data.get("nivel"):
                continue
            data["ano"] = int(data["ano"])
            data["vagas"] = int(data.get("vagas") or 0)
            data["inscritos"] = int(data.get("inscritos") or 0)
            for opt in ("inscricoes_deferidas", "aprovados", "matriculados", "cotistas"):
                if data.get(opt):
                    data[opt] = int(data[opt])
        if model == Egresso:
            for flag in ("ingresso_por_cota", "esta_em_doutorado"):
                if data.get(flag) is not None:
                    data[flag] = str(data[flag]).lower() in ("1", "true", "sim", "s")
            for num in ("ano_ingresso", "ano_conclusao"):
                if data.get(num):
                    data[num] = int(data[num])
        if model == EventoInstitucional:
            if not data.get("nome"):
                continue
            for num in (
                "ano",
                "numero_inscritos",
                "numero_trabalhos",
                "numero_convidados",
            ):
                if data.get(num):
                    data[num] = int(float(data[num]))
            for fl in ("valor_aprovado", "valor_executado"):
                if data.get(fl):
                    data[fl] = float(str(data[fl]).replace(",", "."))

        data["created_at"] = now
        data["updated_at"] = now
        obj = model(**{k: v for k, v in data.items() if v is not None})
        session.add(obj)
        created += 1
    session.commit()
    return {"importados": created}


# --- Eventos institucionais ---
@router.get("/eventos-institucionais", response_model=List[EventoInstitucional])
async def list_eventos_inst(session: Session = Depends(get_session), _user=Depends(require_staff)):
    return list(session.exec(select(EventoInstitucional)).all())


@router.post("/eventos-institucionais", response_model=EventoInstitucional, status_code=201)
async def create_evento_inst(
    item: EventoInstitucional,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/eventos-institucionais/{item_id}", response_model=EventoInstitucional)
async def update_evento_inst(
    item_id: str,
    data: EventoInstitucional,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    db = session.get(EventoInstitucional, item_id)
    if not db:
        raise HTTPException(404, "Evento não encontrado")
    for k, v in data.model_dump(exclude={"id", "created_at"}).items():
        setattr(db, k, v)
    db.updated_at = datetime.utcnow()
    session.add(db)
    session.commit()
    session.refresh(db)
    return db


@router.delete("/eventos-institucionais/{item_id}", status_code=204)
async def delete_evento_inst(
    item_id: str,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    db = session.get(EventoInstitucional, item_id)
    if not db:
        raise HTTPException(404, "Evento não encontrado")
    session.delete(db)
    session.commit()


@router.post("/eventos-institucionais/import-csv")
async def import_eventos_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    content = await file.read()
    return _import_csv(
        session,
        EventoInstitucional,
        content,
        [
            "nome",
            "edicao",
            "ano",
            "tema",
            "local",
            "abrangencia",
            "numero_inscritos",
            "numero_trabalhos",
            "numero_convidados",
            "agencias_financiadoras",
            "valor_aprovado",
            "valor_executado",
            "descricao",
        ],
    )


# --- Egressos ---
@router.get("/egressos", response_model=List[Egresso])
async def list_egressos(session: Session = Depends(get_session), _user=Depends(require_staff)):
    return list(session.exec(select(Egresso)).all())


@router.post("/egressos", response_model=Egresso, status_code=201)
async def create_egresso(
    item: Egresso,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/egressos/{item_id}", status_code=204)
async def delete_egresso(
    item_id: str,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    db = session.get(Egresso, item_id)
    if not db:
        raise HTTPException(404, "Egresso não encontrado")
    session.delete(db)
    session.commit()


@router.post("/egressos/import-csv")
async def import_egressos_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    content = await file.read()
    return _import_csv(
        session,
        Egresso,
        content,
        [
            "nome",
            "ano_ingresso",
            "ano_conclusao",
            "cidade_origem",
            "estado_origem",
            "genero",
            "raca_cor",
            "escola_origem",
            "ingresso_por_cota",
            "atividade_atual",
            "instituicao_atual",
            "cidade_atuacao",
            "estado_atuacao",
            "setor_atuacao",
            "esta_em_doutorado",
            "instituicao_doutorado",
            "impacto_social_resumo",
        ],
    )


# --- Processos seletivos ---
@router.get("/processos-seletivos", response_model=List[ProcessoSeletivo])
async def list_processos(session: Session = Depends(get_session), _user=Depends(require_staff)):
    return list(session.exec(select(ProcessoSeletivo)).all())


@router.post("/processos-seletivos", response_model=ProcessoSeletivo, status_code=201)
async def create_processo(
    item: ProcessoSeletivo,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/processos-seletivos/{item_id}", status_code=204)
async def delete_processo(
    item_id: str,
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    db = session.get(ProcessoSeletivo, item_id)
    if not db:
        raise HTTPException(404, "Processo não encontrado")
    session.delete(db)
    session.commit()


@router.post("/processos-seletivos/import-csv")
async def import_processos_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    _user=Depends(require_staff),
):
    content = await file.read()
    return _import_csv(
        session,
        ProcessoSeletivo,
        content,
        [
            "ano",
            "nivel",
            "vagas",
            "inscritos",
            "inscricoes_deferidas",
            "aprovados",
            "matriculados",
            "cotistas",
            "observacoes",
        ],
    )
