"""Aplica sidecar JSON do Google Acadêmico às produções do docente."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlmodel import Session, select

from app.models.core import Professor
from app.models.data import Producao
from app.services.professor_lookup import find_professor, normalize_text
from app.services.qualis_catalog import normalize_title
from app.services.scholar_profile_parser import (
    ScholarProfileData,
    ScholarProfilePublication,
    default_scholar_profiles_dir,
    parse_scholar_profile_file,
)


@dataclass(frozen=True)
class ScholarProfileLinkage:
    scholar_user_id: str
    professor_id: Optional[str] = None
    id_lattes: Optional[str] = None


def default_linkage_path() -> Path:
    return default_scholar_profiles_dir() / "linkage.json"


def load_scholar_profile_linkage(path: Optional[Path] = None) -> Dict[str, ScholarProfileLinkage]:
    p = path or default_linkage_path()
    if not p.is_file():
        return {}
    raw = json.loads(p.read_text(encoding="utf-8"))
    out: Dict[str, ScholarProfileLinkage] = {}
    for user_id, entry in (raw.get("by_scholar_user_id") or {}).items():
        if not user_id or not isinstance(entry, dict):
            continue
        out[str(user_id)] = ScholarProfileLinkage(
            scholar_user_id=str(user_id),
            professor_id=entry.get("professor_id") or None,
            id_lattes=entry.get("id_lattes") or None,
        )
    return out


def load_profile_json(path: Path) -> ScholarProfileData:
    raw = json.loads(path.read_text(encoding="utf-8"))
    pubs = [
        ScholarProfilePublication(
            title=p["title"],
            authors=p.get("authors"),
            venue=p.get("venue"),
            year=p.get("year"),
            citations=p.get("citations"),
        )
        for p in raw.get("publications") or []
    ]
    metrics_raw = raw.get("metrics") or {}
    from app.services.scholar_profile_parser import ScholarProfileMetrics

    metrics = ScholarProfileMetrics(
        citations_all=int(metrics_raw.get("citations_all") or 0),
        citations_since=metrics_raw.get("citations_since"),
        h_index_all=int(metrics_raw.get("h_index_all") or 0),
        h_index_since=metrics_raw.get("h_index_since"),
        i10_index_all=int(metrics_raw.get("i10_index_all") or 0),
        i10_index_since=metrics_raw.get("i10_index_since"),
        since_year=metrics_raw.get("since_year"),
    )
    return ScholarProfileData(
        scholar_user_id=raw["scholar_user_id"],
        profile_url=raw.get("profile_url"),
        name=raw.get("name") or "",
        affiliation=raw.get("affiliation"),
        interests=list(raw.get("interests") or []),
        metrics=metrics,
        publications=pubs,
        source_html=raw.get("source_html"),
        parsed_at=raw.get("parsed_at") or "",
    )


def _normalize_lattes_id(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\D", "", str(value))


def _name_labels(prof: Professor) -> List[str]:
    labels: List[str] = []
    for raw in (prof.nome_completo, prof.nome_citacao):
        key = normalize_text(raw)
        if key and key not in labels:
            labels.append(key)
    return labels


def resolve_professor_for_profile(
    session: Session,
    profile: ScholarProfileData,
    linkage: Optional[ScholarProfileLinkage] = None,
    *,
    allow_name_match: bool = True,
    min_name_ratio: float = 0.92,
) -> Tuple[Optional[Professor], str]:
    """
    Ordem: linkage (id) → scholar_user_id no docente → nome exato → nome similar (único).
    """
    if linkage and linkage.professor_id:
        prof = session.get(Professor, linkage.professor_id)
        return prof, "linkage_professor_id" if prof else "linkage_invalido"

    profs = list(session.exec(select(Professor)).all())

    if linkage and linkage.id_lattes:
        lid = _normalize_lattes_id(linkage.id_lattes)
        for prof in profs:
            if _normalize_lattes_id(prof.id_lattes) == lid:
                return prof, "linkage_id_lattes"

    for prof in profs:
        if prof.scholar_user_id == profile.scholar_user_id:
            return prof, "scholar_user_id"

    if not allow_name_match or not (profile.name or "").strip():
        return None, "sem_match"

    exact = find_professor(session, nome_completo=profile.name, candidates=profs)
    if exact:
        return exact, "nome_exato"

    scholar_key = normalize_text(profile.name)
    if not scholar_key:
        return None, "sem_match"

    fuzzy_hits: Dict[str, Tuple[Professor, float]] = {}
    for prof in profs:
        best_ratio = 0.0
        for label in _name_labels(prof):
            if label == scholar_key:
                return prof, "nome_exato"
            ratio = SequenceMatcher(None, scholar_key, label).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
        if best_ratio >= min_name_ratio:
            pid = str(prof.id)
            prev = fuzzy_hits.get(pid)
            if not prev or best_ratio > prev[1]:
                fuzzy_hits[pid] = (prof, best_ratio)

    if len(fuzzy_hits) == 1:
        return next(iter(fuzzy_hits.values()))[0], "nome_similar"

    if len(fuzzy_hits) > 1:
        return None, "nome_ambiguo"

    return None, "sem_match"


def _title_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def match_scholar_publication(
    pub: ScholarProfilePublication,
    producoes: List[Producao],
    *,
    min_ratio: float = 0.86,
) -> Tuple[Optional[Producao], str]:
    """Retorna (producao, modo_match) ou (None, 'sem_match'|'ambiguo')."""
    pub_key = normalize_title(pub.title)
    if not pub_key:
        return None, "sem_match"

    exact: List[Producao] = []
    fuzzy: List[Tuple[Producao, float]] = []

    for prod in producoes:
        prod_key = normalize_title(prod.titulo)
        if not prod_key:
            continue
        if prod_key == pub_key:
            exact.append(prod)
            continue
        ratio = _title_similarity(prod_key, pub_key)
        if ratio >= min_ratio:
            if pub.year and prod.ano and pub.year != prod.ano:
                continue
            fuzzy.append((prod, ratio))

    if len(exact) == 1:
        return exact[0], "titulo_exato"
    if len(exact) > 1:
        if pub.year:
            year_hits = [p for p in exact if p.ano == pub.year]
            if len(year_hits) == 1:
                return year_hits[0], "titulo_exato_ano"
        return None, "ambiguo"

    if not fuzzy:
        return None, "sem_match"
    fuzzy.sort(key=lambda x: (-x[1], x[0].ano or 0), reverse=True)
    best_ratio = fuzzy[0][1]
    top = [p for p, r in fuzzy if r >= best_ratio - 0.01]
    if len(top) == 1:
        return top[0], "titulo_similar"
    if pub.year:
        year_hits = [p for p in top if p.ano == pub.year]
        if len(year_hits) == 1:
            return year_hits[0], "titulo_similar_ano"
    return None, "ambiguo"


def apply_scholar_profile_to_professor(
    session: Session,
    professor: Professor,
    profile: ScholarProfileData,
    *,
    clear_unmatched: bool = False,
) -> dict[str, int]:
    stats: Counter = Counter()
    producoes = list(
        session.exec(select(Producao).where(Producao.professor_id == professor.id)).all()
    )
    matched_prod_ids: set[str] = set()

    m = profile.metrics
    professor.scholar_user_id = profile.scholar_user_id
    professor.scholar_citations_total = m.citations_all
    professor.scholar_h_index = m.h_index_all
    professor.scholar_i10_index = m.i10_index_all
    professor.scholar_metrics_since_year = m.since_year
    professor.scholar_profile_synced_at = datetime.now(timezone.utc)
    session.add(professor)

    for pub in profile.publications:
        if pub.citations is None:
            stats["pub_sem_citacoes"] += 1
            continue
        prod, mode = match_scholar_publication(pub, producoes)
        if prod is None:
            stats[mode] += 1
            continue
        matched_prod_ids.add(str(prod.id))
        if prod.scholar_citations == pub.citations:
            stats["ja_ok"] += 1
            continue
        prod.scholar_citations = pub.citations
        session.add(prod)
        stats["atualizado"] += 1
        stats[f"match_{mode}"] += 1

    if clear_unmatched:
        for prod in producoes:
            if str(prod.id) not in matched_prod_ids and prod.scholar_citations is not None:
                prod.scholar_citations = None
                session.add(prod)
                stats["citacoes_removidas"] += 1

    session.commit()

    stats["publicacoes_scholar"] = len(profile.publications)
    stats["producoes_docente"] = len(producoes)
    return dict(stats)


def apply_scholar_profiles_from_dir(
    session: Session,
    *,
    profiles_dir: Optional[Path] = None,
    linkage_path: Optional[Path] = None,
    scholar_user_id: Optional[str] = None,
    clear_unmatched: bool = False,
    allow_name_match: bool = True,
) -> dict[str, Any]:
    base = profiles_dir or default_scholar_profiles_dir()
    json_dir = base / "json"
    linkage = load_scholar_profile_linkage(linkage_path)
    summary: dict[str, Any] = {"perfis": [], "erros": []}

    paths = sorted(json_dir.glob("*.json")) if json_dir.is_dir() else []
    if scholar_user_id:
        paths = [p for p in paths if p.stem == scholar_user_id]

    for path in paths:
        try:
            if path.name.endswith(".raw.json"):
                continue
            profile = load_profile_json(path)
        except Exception as exc:
            summary["erros"].append({"arquivo": str(path), "erro": str(exc)})
            continue

        prof, resolve_mode = resolve_professor_for_profile(
            session,
            profile,
            linkage.get(profile.scholar_user_id),
            allow_name_match=allow_name_match,
        )
        if not prof:
            msg = "professor não encontrado"
            if resolve_mode == "nome_ambiguo":
                msg = (
                    f"vários docentes com nome parecido a «{profile.name}» "
                    "(use linkage.json com professor_id)"
                )
            elif resolve_mode == "linkage_invalido":
                msg = "professor_id em linkage.json inválido"
            summary["erros"].append(
                {
                    "scholar_user_id": profile.scholar_user_id,
                    "scholar_name": profile.name,
                    "resolve_mode": resolve_mode,
                    "erro": msg,
                }
            )
            continue

        stats = apply_scholar_profile_to_professor(
            session,
            prof,
            profile,
            clear_unmatched=clear_unmatched,
        )
        summary["perfis"].append(
            {
                "scholar_user_id": profile.scholar_user_id,
                "scholar_name": profile.name,
                "professor_id": str(prof.id),
                "nome": prof.nome_completo,
                "resolve_mode": resolve_mode,
                **stats,
            }
        )

    return summary


def apply_scholar_profile_from_html(
    session: Session,
    professor: Professor,
    html_path: Path,
    *,
    clear_unmatched: bool = False,
) -> dict[str, int]:
    profile = parse_scholar_profile_file(html_path)
    return apply_scholar_profile_to_professor(
        session, professor, profile, clear_unmatched=clear_unmatched
    )
