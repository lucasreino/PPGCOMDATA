"""Painel de artigos indexados por estrato Qualis, revista e docente."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from sqlmodel import Session, select

from app.models.core import Professor
from app.models.data import Producao
from app.services.producao_coautoria import (
    build_artigo_work_insights,
    group_artigos_by_work,
    is_artigo_tipo,
)

ESTRATO_ORDER = ("A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4", "B5", "C")


def _norm_estrato(raw: Optional[str]) -> str:
    if not raw or not str(raw).strip():
        return "Sem Qualis"
    return str(raw).upper().strip()


def _estrato_sort_key(estrato: str) -> tuple:
    if estrato == "Sem Qualis":
        return (99, estrato)
    try:
        return (ESTRATO_ORDER.index(estrato), estrato)
    except ValueError:
        return (50, estrato)


def build_artigos_qualis_insights(
    session: Session,
    apply_prof: Callable,
    apply_validacao: Callable,
    ano_inicio: Optional[int],
    ano_fim: Optional[int],
) -> Dict[str, Any]:
    stmt = select(Producao)
    stmt = apply_prof(stmt, Producao)
    stmt = apply_validacao(stmt, Producao)
    if ano_inicio is not None:
        stmt = stmt.where(Producao.ano >= ano_inicio)
    if ano_fim is not None:
        stmt = stmt.where(Producao.ano <= ano_fim)

    producoes = session.exec(stmt).all()

    prof_cache: Dict[str, str] = {
        str(p.id): p.nome_completo or "Docente"
        for p in session.exec(select(Professor)).all()
    }

    artigo_rows = [p for p in producoes if is_artigo_tipo(p.tipo)]
    total_registros = len(artigo_rows)
    groups = group_artigos_by_work(artigo_rows)
    obras, participacoes_por_docente = build_artigo_work_insights(groups, prof_cache)

    por_estrato: Dict[str, int] = defaultdict(int)
    por_revista: Dict[str, int] = defaultdict(int)
    prof_estrato: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    artigos: List[Dict[str, Any]] = []

    for obra in obras:
        estrato = _norm_estrato(obra.get("qualis"))
        veiculo = obra["veiculo"]
        por_estrato[estrato] += 1
        por_revista[veiculo] += 1

        for nome in obra["docentes_ppgcom"]:
            prof_estrato[nome][estrato] += 1

        artigos.append(
            {
                "id": obra["id"],
                "professor_id": obra["professor_id"],
                "professor_nome": obra["professor_nome"],
                "titulo": obra["titulo"],
                "veiculo": veiculo,
                "qualis": estrato if estrato != "Sem Qualis" else None,
                "scholar_h5_index": obra.get("scholar_h5_index"),
                "scholar_h5_median": obra.get("scholar_h5_median"),
                "scholar_metrics_year": obra.get("scholar_metrics_year"),
                "ano": obra["ano"],
                "doi": obra["doi"],
                "docentes_ppgcom": obra["docentes_ppgcom"],
                "num_docentes_ppgcom": obra["num_docentes_ppgcom"],
                "eh_coautoria": obra["eh_coautoria"],
                "autores_lattes": obra.get("autores_lattes"),
            }
        )

    total = len(obras)
    com_qualis = sum(1 for a in artigos if a.get("qualis"))
    estratos_sorted = sorted(por_estrato.keys(), key=_estrato_sort_key)

    por_estrato_pct: Dict[str, Dict[str, Any]] = {}
    for e in estratos_sorted:
        n = por_estrato[e]
        por_estrato_pct[e] = {
            "count": n,
            "percent": round((n / total) * 100, 1) if total else 0.0,
        }

    revistas_top = sorted(por_revista.items(), key=lambda x: (-x[1], x[0]))[:25]
    por_revista_list = [
        {"veiculo": v, "count": c, "percent": round((c / total) * 100, 1) if total else 0}
        for v, c in revistas_top
    ]

    professor_por_estrato: Dict[str, Dict[str, int]] = {}
    for nome, counts in prof_estrato.items():
        professor_por_estrato[nome] = {
            e: counts.get(e, 0) for e in estratos_sorted if counts.get(e, 0)
        }

    publicacoes_por_docente = sorted(
        participacoes_por_docente.items(),
        key=lambda x: (-x[1], x[0]),
    )

    return {
        "total_artigos": total,
        "total_registros": total_registros,
        "com_qualis": com_qualis,
        "sem_qualis": total - com_qualis,
        "estratos": estratos_sorted,
        "por_estrato": por_estrato_pct,
        "por_revista": por_revista_list,
        "professor_por_estrato": professor_por_estrato,
        "publicacoes_por_docente": [
            {"docente": nome, "publicacoes": n} for nome, n in publicacoes_por_docente
        ],
        "artigos": artigos[:120],
    }
