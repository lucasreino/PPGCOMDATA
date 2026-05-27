"""Carrega e consulta snapshot de h-index de revistas (ISSN / título → h_index)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlmodel import select

from app.models.data import Producao
from app.services.qualis_catalog import normalize_issn, normalize_title


@dataclass(frozen=True)
class JournalHindexHit:
    h_index: float


def default_journal_hindex_json_path() -> Path:
    here = Path(__file__).resolve()
    candidates: list[Path] = [
        Path("/workspace/data/journal_hindex/revistas-hindex-comunicacao.json"),
    ]
    if len(here.parents) > 2:
        candidates.append(
            here.parents[2] / "data" / "journal_hindex" / "revistas-hindex-comunicacao.json"
        )
    if len(here.parents) > 4:
        candidates.append(
            here.parents[4] / "data" / "journal_hindex" / "revistas-hindex-comunicacao.json"
        )
    candidates.append(
        Path.cwd() / "data" / "journal_hindex" / "revistas-hindex-comunicacao.json"
    )
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


def default_journal_hindex_manual_overrides_path() -> Path:
    here = Path(__file__).resolve()
    candidates: list[Path] = [
        Path("/workspace/data/journal_hindex/manual_overrides.json"),
    ]
    if len(here.parents) > 2:
        candidates.append(
            here.parents[2] / "data" / "journal_hindex" / "manual_overrides.json"
        )
    if len(here.parents) > 4:
        candidates.append(
            here.parents[4] / "data" / "journal_hindex" / "manual_overrides.json"
        )
    candidates.append(Path.cwd() / "data" / "journal_hindex" / "manual_overrides.json")
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


def _parse_hit(raw: Any) -> Optional[JournalHindexHit]:
    if not isinstance(raw, dict):
        return None
    h = raw.get("h_index")
    if h is None or h == "":
        return None
    try:
        h_index = float(h)
    except (TypeError, ValueError):
        return None
    if h_index < 0:
        return None
    return JournalHindexHit(h_index=h_index)


def load_journal_hindex_manual_overrides(
    path: Optional[Path] = None,
) -> Tuple[Dict[str, JournalHindexHit], Dict[str, JournalHindexHit]]:
    p = path or default_journal_hindex_manual_overrides_path()
    if not p.is_file():
        return {}, {}
    raw = json.loads(p.read_text(encoding="utf-8"))
    by_issn: Dict[str, JournalHindexHit] = {}
    by_veiculo: Dict[str, JournalHindexHit] = {}
    for key, val in (raw.get("by_issn") or {}).items():
        issn_key = normalize_issn(key)
        hit = _parse_hit(val if isinstance(val, dict) else {"h_index": val})
        if issn_key and hit:
            by_issn[issn_key] = hit
    for key, val in (raw.get("by_veiculo") or {}).items():
        titulo_key = normalize_title(key)
        hit = _parse_hit(val if isinstance(val, dict) else {"h_index": val})
        if titulo_key and hit:
            by_veiculo[titulo_key] = hit
    return by_issn, by_veiculo


def load_journal_hindex_catalog(
    json_path: Path,
) -> Tuple[Dict[str, JournalHindexHit], Dict[str, JournalHindexHit]]:
    """Retorna (by_issn, by_titulo). Último título normalizado vence se houver duplicata."""
    if not json_path.is_file():
        return {}, {}
    data = json.loads(json_path.read_text(encoding="utf-8"))
    by_issn: Dict[str, JournalHindexHit] = {}
    by_titulo: Dict[str, JournalHindexHit] = {}
    journals: List[Any] = list(data.get("journals") or [])
    for row in journals:
        if not isinstance(row, dict):
            continue
        hit = _parse_hit(row)
        if not hit:
            continue
        issn_key = normalize_issn(row.get("issn"))
        titulo_key = normalize_title(row.get("titulo"))
        if issn_key:
            by_issn[issn_key] = hit
        if titulo_key:
            by_titulo[titulo_key] = hit
    return by_issn, by_titulo


def load_journal_hindex_from_csv(csv_path: Path) -> Dict[str, Any]:
    """Converte CSV (nome, issn, h_index, …) em estrutura de snapshot JSON."""
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    seen_issn: set[str] = set()
    journals: list[dict[str, Any]] = []
    for row in rows:
        h_raw = (row.get("h_index") or "").strip()
        if not h_raw:
            continue
        try:
            h_index = float(h_raw)
        except ValueError:
            continue
        issn = (row.get("issn") or "").strip()
        titulo = (row.get("nome_corrigido") or row.get("nome") or "").strip()
        if issn and issn in seen_issn:
            continue
        if issn:
            seen_issn.add(issn)
        journals.append(
            {
                "titulo": titulo,
                "issn": issn or None,
                "h_index": h_index,
            }
        )
    return {
        "source_note": f"Gerado a partir de {csv_path.name}",
        "source_csv": csv_path.name,
        "journals": journals,
    }


def lookup_journal_hindex(
    issn: Optional[str],
    veiculo: Optional[str],
    by_issn: Dict[str, JournalHindexHit],
    by_titulo: Dict[str, JournalHindexHit],
    manual_issn: Optional[Dict[str, JournalHindexHit]] = None,
    manual_veiculo: Optional[Dict[str, JournalHindexHit]] = None,
) -> Tuple[Optional[JournalHindexHit], str]:
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


def _producao_matches_hit(prod: Producao, hit: JournalHindexHit) -> bool:
    if prod.journal_h_index is None:
        return False
    return abs(prod.journal_h_index - hit.h_index) < 1e-9


def apply_journal_hindex_to_producoes(
    session,
    *,
    tipos: frozenset[str] | None = None,
    json_path: Path | None = None,
) -> dict[str, int]:
    """Cruza artigos/anais com o snapshot de h-index de revistas."""
    from collections import Counter

    path = json_path or default_journal_hindex_json_path()
    if not path.is_file():
        return {"atualizado": 0, "ja_ok": 0, "sem_match": 0}

    by_issn, by_titulo = load_journal_hindex_catalog(path)
    if not by_issn and not by_titulo:
        return {"atualizado": 0, "ja_ok": 0, "sem_match": 0}

    manual_issn, manual_veiculo = load_journal_hindex_manual_overrides()
    allowed = tipos or frozenset({"artigo", "anais"})
    stats: Counter = Counter()

    for prod in session.exec(select(Producao)).all():
        if (prod.tipo or "").lower() not in allowed:
            continue
        hit, _ = lookup_journal_hindex(
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
        prod.journal_h_index = hit.h_index
        session.add(prod)
        stats["atualizado"] += 1

    if stats["atualizado"]:
        session.commit()

    return {
        "atualizado": stats["atualizado"],
        "ja_ok": stats["ja_ok"],
        "sem_match": stats["sem_match"],
    }
