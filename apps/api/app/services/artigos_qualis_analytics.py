"""Painel de artigos indexados por estrato Qualis, revista e docente."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Type

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.core import Professor
from app.models.data import Producao

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


def _is_artigo(tipo: Optional[str]) -> bool:
    return (tipo or "").lower().strip() in ("artigo", "artigos")


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

    artigos: List[Dict[str, Any]] = []
    por_estrato: Dict[str, int] = defaultdict(int)
    por_revista: Dict[str, int] = defaultdict(int)
    prof_estrato: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    prof_nomes: Dict[str, str] = {}

    for prod in producoes:
        pid = str(prod.professor_id)
        nome = prof_cache.get(pid, "Docente")
        if not _is_artigo(prod.tipo):
            continue
        estrato = _norm_estrato(prod.qualis)
        veiculo = (prod.veiculo or "Revista não informada").strip()
        prof_nomes[pid] = nome

        por_estrato[estrato] += 1
        por_revista[veiculo] += 1
        prof_estrato[pid][estrato] += 1

        artigos.append(
            {
                "id": str(prod.id),
                "professor_id": pid,
                "professor_nome": prof_nomes[pid],
                "titulo": prod.titulo,
                "veiculo": veiculo,
                "qualis": estrato if estrato != "Sem Qualis" else None,
                "ano": prod.ano,
                "doi": prod.doi,
            }
        )

    total = len(artigos)
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
    for pid, counts in prof_estrato.items():
        label = prof_nomes.get(pid, pid)
        professor_por_estrato[label] = {
            e: counts.get(e, 0) for e in estratos_sorted if counts.get(e, 0)
        }

    artigos.sort(key=lambda a: (a.get("ano") or 0), reverse=True)

    return {
        "total_artigos": total,
        "com_qualis": com_qualis,
        "sem_qualis": total - com_qualis,
        "estratos": estratos_sorted,
        "por_estrato": por_estrato_pct,
        "por_revista": por_revista_list,
        "professor_por_estrato": professor_por_estrato,
        "artigos": artigos[:120],
    }
