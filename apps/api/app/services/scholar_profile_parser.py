"""Parse HTML exportado do Google Acadêmico (perfil de autor)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any, List, Optional
from xml.etree import ElementTree as ET

# Ordem fixa das linhas na tabela de métricas do Scholar.
_METRIC_ROW_KEYS = ("citations", "h_index", "i10_index")

_UNICODE_BIDI = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069\ufeff]")


def _clean_text(raw: str) -> str:
    text = unescape(raw or "")
    text = _UNICODE_BIDI.sub("", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def _parse_int(raw: str) -> Optional[int]:
    s = _clean_text(raw).replace(".", "").replace(",", "")
    if not s or s in {"—", "-", "–"}:
        return None
    try:
        return int(s)
    except ValueError:
        return None


@dataclass
class ScholarProfileMetrics:
    citations_all: int
    citations_since: Optional[int]
    h_index_all: int
    h_index_since: Optional[int]
    i10_index_all: int
    i10_index_since: Optional[int]
    since_year: Optional[int] = None


@dataclass
class ScholarProfilePublication:
    title: str
    authors: Optional[str] = None
    venue: Optional[str] = None
    year: Optional[int] = None
    citations: Optional[int] = None


@dataclass
class ScholarProfileData:
    scholar_user_id: str
    profile_url: Optional[str]
    name: str
    affiliation: Optional[str]
    interests: List[str] = field(default_factory=list)
    metrics: ScholarProfileMetrics = field(
        default_factory=lambda: ScholarProfileMetrics(0, None, 0, None, 0, None)
    )
    publications: List[ScholarProfilePublication] = field(default_factory=list)
    source_html: Optional[str] = None
    parsed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_scholar_profiles_dir() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        Path("/workspace/data/scholar_profiles"),
        here.parents[2] / "data" / "scholar_profiles" if len(here.parents) > 2 else None,
        here.parents[4] / "data" / "scholar_profiles" if len(here.parents) > 4 else None,
        Path.cwd() / "data" / "scholar_profiles",
    ]
    for p in candidates:
        if p and p.is_dir():
            return p
    return Path.cwd() / "data" / "scholar_profiles"


def _extract_user_id(html: str) -> Optional[str]:
    m = re.search(r"citations\?user=([A-Za-z0-9_-]+)", html)
    if m:
        return m.group(1)
    m = re.search(r"<!-- saved from url=.*?user=([A-Za-z0-9_-]+)", html, re.I)
    return m.group(1) if m else None


def _extract_profile_url(html: str, user_id: str) -> Optional[str]:
    m = re.search(
        r'<!--\s*saved from url=\(\d+\)(https?://[^\s>]+citations\?user=[^"&\s>]+)',
        html,
        re.I,
    )
    if m:
        return unescape(m.group(1))
    return f"https://scholar.google.com/citations?user={user_id}"


def _extract_name(html: str) -> str:
    m = re.search(r'property="og:title"\s+content="([^"]+)"', html, re.I)
    if m:
        return _clean_text(m.group(1))
    m = re.search(r"<title>([^<]+)</title>", html, re.I)
    if m:
        title = _clean_text(m.group(1))
        return title.split(" - ")[0].strip()
    return ""


def _parse_og_description(html: str) -> tuple[Optional[str], List[str]]:
    m = re.search(r'property="og:description"\s+content="([^"]+)"', html, re.I)
    if not m:
        return None, []
    parts = [_clean_text(p) for p in re.split(r"\s*-\s*", _clean_text(m.group(1)))]
    parts = [p for p in parts if p]
    if not parts:
        return None, []
    affiliation = parts[0]
    interests: list[str] = []
    for p in parts[1:]:
        low = p.lower()
        if low.startswith("citado por") or low.startswith("cited by"):
            continue
        interests.append(p)
    return affiliation, interests


def _parse_since_year(html: str) -> Optional[int]:
    tbl = re.search(r'id="gsc_rsb_st".*?</table>', html, re.S | re.I)
    if not tbl:
        return None
    m = re.search(r"Desde\s+(\d{4})|Since\s+(\d{4})", tbl.group(0), re.I)
    if not m:
        return None
    return int(m.group(1) or m.group(2))


def _parse_metrics(html: str) -> ScholarProfileMetrics:
    tbl = re.search(r'id="gsc_rsb_st".*?</table>', html, re.S | re.I)
    if not tbl:
        raise ValueError("Tabela de métricas (#gsc_rsb_st) não encontrada no HTML")
    since_year = _parse_since_year(html)
    rows: list[tuple[int, Optional[int]]] = []
    for row_html in re.findall(r"<tr[^>]*>.*?</tr>", tbl.group(0), re.S | re.I):
        nums = [
            _parse_int(x)
            for x in re.findall(r'class="gsc_rsb_std"[^>]*>([^<]*)<', row_html, re.I)
        ]
        nums = [n for n in nums if n is not None]
        if len(nums) >= 2:
            rows.append((nums[0], nums[1]))
        elif len(nums) == 1:
            rows.append((nums[0], None))
    while len(rows) < 3:
        rows.append((0, None))
    vals = {key: rows[i] for i, key in enumerate(_METRIC_ROW_KEYS)}
    return ScholarProfileMetrics(
        citations_all=vals["citations"][0],
        citations_since=vals["citations"][1],
        h_index_all=vals["h_index"][0],
        h_index_since=vals["h_index"][1],
        i10_index_all=vals["i10_index"][0],
        i10_index_since=vals["i10_index"][1],
        since_year=since_year,
    )


def _parse_publications(html: str) -> List[ScholarProfilePublication]:
    pubs: list[ScholarProfilePublication] = []
    for row in re.findall(r'<tr class="gsc_a_tr".*?</tr>', html, re.S | re.I):
        title_m = re.search(r'class="gsc_a_at"[^>]*>(.*?)<', row, re.S | re.I)
        if not title_m:
            continue
        title = _clean_text(title_m.group(1))
        if not title:
            continue
        grays = [
            _clean_text(g)
            for g in re.findall(r'<div class="gs_gray">(.*?)</div>', row, re.S | re.I)
        ]
        authors = grays[0] if grays else None
        venue = grays[1] if len(grays) > 1 else None
        year_m = re.search(
            r'class="gsc_a_y[^"]*"[^>]*>.*?<span[^>]*>(\d{4})</span>', row, re.S | re.I
        )
        year = int(year_m.group(1)) if year_m else None
        cite_m = re.search(r'class="gsc_a_ac[^"]*"[^>]*>([^<]*)<', row, re.I)
        citations = _parse_int(cite_m.group(1)) if cite_m else None
        pubs.append(
            ScholarProfilePublication(
                title=title,
                authors=authors,
                venue=venue,
                year=year,
                citations=citations,
            )
        )
    return pubs


def parse_scholar_profile_html(
    html: str,
    *,
    source_html: Optional[str] = None,
) -> ScholarProfileData:
    user_id = _extract_user_id(html)
    if not user_id:
        raise ValueError("ID do perfil Scholar (user=...) não encontrado no HTML")

    name = _extract_name(html)
    if not name:
        raise ValueError("Nome do autor não encontrado no HTML")

    affiliation, interests = _parse_og_description(html)
    metrics = _parse_metrics(html)
    publications = _parse_publications(html)

    return ScholarProfileData(
        scholar_user_id=user_id,
        profile_url=_extract_profile_url(html, user_id),
        name=name,
        affiliation=affiliation,
        interests=interests,
        metrics=metrics,
        publications=publications,
        source_html=source_html,
        parsed_at=datetime.now(timezone.utc).isoformat(),
    )


def parse_scholar_profile_file(path: Path) -> ScholarProfileData:
    html = path.read_text(encoding="utf-8", errors="replace")
    return parse_scholar_profile_html(html, source_html=str(path.resolve()))


def write_scholar_profile_json(data: ScholarProfileData, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_scholar_profile_xml(data: ScholarProfileData, path: Path) -> None:
    root = ET.Element(
        "scholarProfile",
        {
            "scholarUserId": data.scholar_user_id,
            "parsedAt": data.parsed_at,
        },
    )
    if data.profile_url:
        root.set("profileUrl", data.profile_url)
    if data.source_html:
        root.set("sourceHtml", data.source_html)

    author = ET.SubElement(root, "author", {"name": data.name})
    if data.affiliation:
        author.set("affiliation", data.affiliation)
    for interest in data.interests:
        ET.SubElement(author, "interest").text = interest

    m = data.metrics
    ET.SubElement(
        root,
        "metrics",
        {
            "sinceYear": str(m.since_year or ""),
            "citationsAll": str(m.citations_all),
            "citationsSince": str(m.citations_since if m.citations_since is not None else ""),
            "hIndexAll": str(m.h_index_all),
            "hIndexSince": str(m.h_index_since if m.h_index_since is not None else ""),
            "i10IndexAll": str(m.i10_index_all),
            "i10IndexSince": str(m.i10_index_since if m.i10_index_since is not None else ""),
        },
    )

    pubs_el = ET.SubElement(root, "publications", {"count": str(len(data.publications))})
    for pub in data.publications:
        attrs: dict[str, str] = {"title": pub.title}
        if pub.year is not None:
            attrs["year"] = str(pub.year)
        if pub.citations is not None:
            attrs["citations"] = str(pub.citations)
        item = ET.SubElement(pubs_el, "publication", attrs)
        if pub.authors:
            ET.SubElement(item, "authors").text = pub.authors
        if pub.venue:
            ET.SubElement(item, "venue").text = pub.venue

    path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
