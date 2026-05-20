from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.auth import require_staff
from app.database import get_session
from app.services.export_service import ExportService
from app.services.indicator_service import IndicatorFilters, IndicatorService
from app.services.narrative_service import NarrativeService

router = APIRouter(prefix="/dossie-apcn", tags=["Dossiê APCN"])


def _filters(
    professor_id: Optional[str] = None,
    linha_pesquisa_id: Optional[str] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
    apenas_validados: bool = Query(False, description="Contar só registros confirmados/editados"),
) -> IndicatorFilters:
    return IndicatorFilters(
        professor_id=professor_id,
        linha_pesquisa_id=linha_pesquisa_id,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        apenas_validados=apenas_validados,
    )


def _svc(session: Session, filters: IndicatorFilters) -> IndicatorService:
    return IndicatorService(session, filters)


@router.get("/overview")
async def dossie_overview(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return _svc(session, filters).get_overview_indicators()


@router.get("/corpo-docente")
async def dossie_corpo_docente(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return _svc(session, filters).get_corpo_docente_indicators()


@router.get("/producao")
async def dossie_producao(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return _svc(session, filters).get_production_indicators()


@router.get("/projetos")
async def dossie_projetos(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return _svc(session, filters).get_project_indicators()


@router.get("/financiamento")
async def dossie_financiamento(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return _svc(session, filters).get_financing_indicators()


@router.get("/eventos")
async def dossie_eventos(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return _svc(session, filters).get_event_indicators()


@router.get("/lacunas")
async def dossie_lacunas(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return _svc(session, filters).get_gap_indicators()


@router.get("/professor/{professor_id}")
async def dossie_professor(
    professor_id: str,
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    data = _svc(session, filters).get_teacher_indicators(professor_id)
    if data.get("erro"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=data["erro"])
    return data


@router.get("/linha/{linha_pesquisa_id}")
async def dossie_linha(
    linha_pesquisa_id: str,
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    data = _svc(session, filters).get_line_indicators(linha_pesquisa_id)
    if data.get("erro"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=data["erro"])
    return data


@router.get("/egressos")
async def dossie_egressos(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return _svc(session, filters).get_egress_indicators()


@router.get("/demanda")
async def dossie_demanda(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return _svc(session, filters).get_selection_indicators()


@router.get("/narrativas")
async def dossie_narrativas(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return NarrativeService(session, filters).generate_all()


def _export_csv(session: Session, filters: IndicatorFilters, kind: str) -> str:
    exp = ExportService(session, filters)
    return {
        "producao": exp.producao_csv,
        "financiamento": exp.financiamento_csv,
        "projetos": exp.projetos_csv,
        "eventos": exp.eventos_csv,
        "lacunas": exp.lacunas_csv,
        "egressos": exp.egressos_csv,
    }[kind]()


@router.get("/export/producao.csv")
async def export_producao_csv(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return Response(
        content=_export_csv(session, filters, "producao"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=producao_docente.csv"},
    )


@router.get("/export/financiamento.csv")
async def export_financiamento_csv(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return Response(
        content=_export_csv(session, filters, "financiamento"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=financiamento.csv"},
    )


@router.get("/export/projetos.csv")
async def export_projetos_csv(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return Response(
        content=_export_csv(session, filters, "projetos"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=projetos.csv"},
    )


@router.get("/export/eventos.csv")
async def export_eventos_csv(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return Response(
        content=_export_csv(session, filters, "eventos"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=eventos.csv"},
    )


@router.get("/export/lacunas.csv")
async def export_lacunas_csv(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return Response(
        content=_export_csv(session, filters, "lacunas"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=lacunas.csv"},
    )


@router.get("/export/egressos.csv")
async def export_egressos_csv(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    return Response(
        content=_export_csv(session, filters, "egressos"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=egressos.csv"},
    )


@router.get("/export/resumo.md")
async def export_resumo_md(
    session: Session = Depends(get_session),
    filters: IndicatorFilters = Depends(_filters),
    _user=Depends(require_staff),
):
    md = ExportService(session, filters).resumo_markdown()
    return Response(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=resumo_ppgcom.md"},
    )
