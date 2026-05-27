"""Carrega e consulta snapshot Google Scholar Metrics (ISSN / título → h5)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlmodel import select

from app.models.data import Producao
from app.services.qualis_catalog import normalize_issn, normalize_title


@dataclass(frozen=True)
class ScholarMetricsHit:
    h5_index: int
    h5_median: Optional[int]
    metrics_year: int


def default_scholar_metrics_json_path() -> Path:
    here = Path(__file__).resolve()
    candidates: list[Path] = [
        Path("/workspace/data/scholar_metrics/scholar-metrics-comunicacao.json"),
    ]
    if len(here.parents) > 2:
        candidates.append(
            here.parents[2] / "data" / "scholar_metrics" / "scholar-metrics-comunicacao.json"
        )
    if len(here.parents) > 4:
        candidates.append(
            here.parents[4] / "data" / "scholar_metrics" / "scholar-metrics-comunicacao.json"
        )
    candidates.append(Path.cwd() / "data" / "scholar_metrics" / "scholar-metrics-comunicacao.json")
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


def default_scholar_manual_overrides_path() -> Path:
    here = Path(__file__).resolve()
    candidates: list[Path] = [
        Path("/workspace/data/scholar_metrics/manual_overrides.json"),
    ]
    if len(here.parents) > 2:
        candidates.append(
            here.parents[2] / "data" / "scholar_metrics" / "manual_overrides.json"
        )
    if len(here.parents) > 4:
        candidates.append(
            here.parents[4] / "data" / "scholar_metrics" / "manual_overrides.json"
        )
    candidates.append(Path.cwd() / "data" / "scholar_metrics" / "manual_overrides.json")
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


def _parse_hit(raw: Any, fallback_year: int) -> Optional[ScholarMetricsHit]:
    if not isinstance(raw, dict):
        return None
    h5 = raw.get("h5_index")
    if h5 is None:
        return None
    try:
        h5_index = int(h5)
    except (TypeError, ValueError):
        return None
    h5_med = raw.get("h5_median")
    h5_median: Optional[int]
    if h5_med is None or h5_med == "":
        h5_median = None
    else:
        try:
            h5_median = int(h5_med)
        except (TypeError, ValueError):
            return None
    if raw.get("metrics_year") is None or raw.get("metrics_year") == "":
        metrics_year = int(fallback_year) if fallback_year else 0
    else:
        try:
            metrics_year = int(raw.get("metrics_year"))
        except (TypeError, ValueError):
            metrics_year = int(fallback_year) if fallback_year else 0
    if metrics_year <= 0:
        return None
    return ScholarMetricsHit(
        h5_index=h5_index,
        h5_median=h5_median,
        metrics_year=metrics_year,
    )


def load_scholar_manual_overrides(
    path: Optional[Path] = None,
    *,
    fallback_metrics_year: int = 0,
) -> Tuple[Dict[str, ScholarMetricsHit], Dict[str, ScholarMetricsHit]]:
    p = path or default_scholar_manual_overrides_path()
    if not p.is_file():
        return {}, {}
    raw = json.loads(p.read_text(encoding="utf-8"))
    by_issn: Dict[str, ScholarMetricsHit] = {}
    by_veiculo: Dict[str, ScholarMetricsHit] = {}
    for key, val in (raw.get("by_issn") or {}).items():
        issn_key = normalize_issn(key)
        hit = _parse_hit(val, fallback_metrics_year)
        if issn_key and hit:
            by_issn[issn_key] = hit
    for key, val in (raw.get("by_veiculo") or {}).items():
        titulo_key = normalize_title(key)
        hit = _parse_hit(val, fallback_metrics_year)
        if titulo_key and hit:
            by_veiculo[titulo_key] = hit
    return by_issn, by_veiculo


def load_scholar_metrics_catalog(
    json_path: Path,
) -> Tuple[Dict[str, ScholarMetricsHit], Dict[str, ScholarMetricsHit], int]:
    """
    Retorna (by_issn, by_titulo, metrics_year_default).
    Último título normalizado vence se houver duplicata.
    """
    if not json_path.is_file():
        return {}, {}, 0
    data = json.loads(json_path.read_text(encoding="utf-8"))
    default_year = int(data.get("metrics_year") or 0)
    by_issn: Dict[str, ScholarMetricsHit] = {}
    by_titulo: Dict[str, ScholarMetricsHit] = {}
    journals: List[Any] = list(data.get("journals") or [])
    for row in journals:
        if not isinstance(row, dict):
            continue
        hit = _parse_hit(row, default_year)
        if not hit:
            continue
        issn_key = normalize_issn(row.get("issn"))
        titulo_key = normalize_title(row.get("titulo"))
        if issn_key:
            by_issn[issn_key] = hit
        if titulo_key:
            by_titulo[titulo_key] = hit
    return by_issn, by_titulo, default_year


def lookup_scholar_metrics(
    issn: Optional[str],
    veiculo: Optional[str],
    by_issn: Dict[str, ScholarMetricsHit],
    by_titulo: Dict[str, ScholarMetricsHit],
    manual_issn: Optional[Dict[str, ScholarMetricsHit]] = None,
    manual_veiculo: Optional[Dict[str, ScholarMetricsHit]] = None,
) -> Tuple[Optional[ScholarMetricsHit], str]:
    issn_key = normalize_issn(issn)
    veic_key = normalize_title(veiculo)

    if manual_issn and issn_key and issn_key in manual_issn:
        return manual_issn[issn_key], "manual_issn"
    if manual_veiculo and veic_key and veic_key in manual_veiculo:
        return manual_veiculo[veic_key], "manual_veiculo"

    if issn_key and issn_key in by_issn:
        return by_issn[issn_key], "issn"

    if not veic_key:
        return None, "none"

    if veic_key in by_titulo:
        return by_titulo[veic_key], "titulo_exato"

    for cat_key, hit in by_titulo.items():
        if len(cat_key) < 8 or len(veic_key) < 8:
            continue
        if cat_key in veic_key or veic_key in cat_key:
            return hit, "titulo_parcial"

    return None, "none"


def _producao_matches_hit(prod: Producao, hit: ScholarMetricsHit) -> bool:
    return (
        prod.scholar_h5_index == hit.h5_index
        and prod.scholar_h5_median == hit.h5_median
        and prod.scholar_metrics_year == hit.metrics_year
    )


def apply_scholar_metrics_to_producoes(
    session,
    *,
    tipos: frozenset[str] | None = None,
    json_path: Path | None = None,
) -> dict[str, int]:
    """Cruza artigos/anais com o snapshot Scholar Metrics e grava h5 em Producao."""
    from collections import Counter

    path = json_path or default_scholar_metrics_json_path()
    if not path.is_file():
        return {"atualizado": 0, "ja_ok": 0, "sem_match": 0}

    by_issn, by_titulo, file_year = load_scholar_metrics_catalog(path)
    if not by_issn and not by_titulo:
        return {"atualizado": 0, "ja_ok": 0, "sem_match": 0}

    manual_issn, manual_veiculo = load_scholar_manual_overrides(
        fallback_metrics_year=file_year,
    )
    allowed = tipos or frozenset({"artigo", "anais"})
    stats: Counter = Counter()

    for prod in session.exec(select(Producao)).all():
        if (prod.tipo or "").lower() not in allowed:
            continue
        hit, _ = lookup_scholar_metrics(
            prod.issn,
            prod.veiculo,
            by_issn,
            by_titulo,
            manual_issn,
            manual_veiculo,
        )
        if not hit:
            stats["sem_match"] += 1
            continue
        if _producao_matches_hit(prod, hit):
            stats["ja_ok"] += 1
            continue
        prod.scholar_h5_index = hit.h5_index
        prod.scholar_h5_median = hit.h5_median
        prod.scholar_metrics_year = hit.metrics_year
        session.add(prod)
        stats["atualizado"] += 1

    if stats["atualizado"]:
        session.commit()

    return {
        "atualizado": stats["atualizado"],
        "ja_ok": stats["ja_ok"],
        "sem_match": stats["sem_match"],
    }
