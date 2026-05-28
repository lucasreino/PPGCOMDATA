"""Parse COMPÓS revistas (Google Scholar H 2021/2022) and merge with PPG catalog."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "apps" / "api"))

from app.services.journal_hindex_catalog import load_journal_hindex_from_csv
from app.services.qualis_catalog import normalize_issn, normalize_title


def extract_raw_journals_data(html: str) -> str:
    m = re.search(
        r"const rawJournalsData = `([^`]+)`",
        html,
        re.S,
    )
    if not m:
        raise ValueError("rawJournalsData not found in HTML")
    return m.group(1).strip()


def _split_metrics(metrics: str) -> tuple[int, int, int, int] | None:
    """Partition concatenated digits into 4 metrics (1–2 digits each)."""
    if not metrics:
        return None
    if metrics.count("-") == len(metrics) and len(metrics) == 4:
        return tuple(0 if c == "-" else int(c) for c in metrics)

    if len(metrics) == 4 and metrics.isdigit():
        return tuple(int(c) for c in metrics)

    best: tuple[int, int, int, int] | None = None
    best_score = -1

    def score_quad(vals: tuple[int, int, int, int]) -> int:
        s = 100
        for i, v in enumerate(vals):
            if v <= 0:
                s -= 50
            if i in (0, 2) and v > 30:
                s -= 40
            if i in (1, 3) and v > 50:
                s -= 10
        return s

    def dfs(pos: int, parts: list[int]) -> None:
        nonlocal best, best_score
        if len(parts) == 4:
            if pos == len(metrics):
                quad = (parts[0], parts[1], parts[2], parts[3])
                sc = score_quad(quad)
                if sc > best_score or (
                    sc == best_score
                    and best is not None
                    and (quad[0] + quad[2]) < (best[0] + best[2])
                ):
                    best_score = sc
                    best = quad
            return
        if pos >= len(metrics) or len(parts) >= 4:
            return
        for width in (1, 2):
            if pos + width > len(metrics):
                continue
            chunk = metrics[pos : pos + width]
            if chunk.startswith("0") and width == 2:
                continue
            dfs(pos + width, parts + [int(chunk)])

    dfs(0, [])
    return best


def parse_compos_line(line: str) -> dict:
    line = line.strip().rstrip(".")
    if not line:
        raise ValueError("empty line")

    m = re.match(r"^(.+?)([0-9\-]+)$", line)
    if not m:
        return {
            "titulo": line,
            "h_2021": None,
            "mh5_2021": None,
            "h_2022": None,
            "mh5_2022": None,
        }

    revista = m.group(1).strip()
    metrics = m.group(2)
    if set(metrics) == {"-"}:
        return {
            "titulo": revista,
            "h_2021": None,
            "mh5_2021": None,
            "h_2022": None,
            "mh5_2022": None,
        }

    quad = _split_metrics(metrics)
    if not quad:
        return {
            "titulo": revista,
            "h_2021": None,
            "mh5_2021": None,
            "h_2022": None,
            "mh5_2022": None,
        }

    h21, mh21, h22, mh22 = quad
    return {
        "titulo": revista,
        "h_2021": h21 or None,
        "mh5_2021": mh21 or None,
        "h_2022": h22 or None,
        "mh5_2022": mh22 or None,
    }


def parse_compos_html(html_path: Path) -> list[dict]:
    html = html_path.read_text(encoding="utf-8")
    raw = extract_raw_journals_data(html)
    lines = [ln for ln in raw.split("\n") if ln.strip()]
    return [parse_compos_line(ln) for ln in lines]


def choose_h(row: dict, *, prefer_year: int = 2022) -> float | None:
    if prefer_year == 2022:
        h = row.get("h_2022")
        if h is not None:
            return float(h)
    h = row.get("h_2021")
    return float(h) if h is not None else None


def match_compos(
    nome: str, by_norm: dict[str, dict]
) -> dict | None:
    key = normalize_title(nome)
    if key in by_norm:
        return by_norm[key]
    for ck, cj in by_norm.items():
        if len(key) >= 8 and (key in ck or ck in key):
            return cj
    return None


def build_compos_json(journals: list[dict]) -> dict:
    entries = []
    for j in journals:
        h = choose_h(j)
        if h is None:
            continue
        entries.append(
            {
                "titulo": j["titulo"],
                "issn": None,
                "h_index": h,
                "h_2021": j.get("h_2021"),
                "h_2022": j.get("h_2022"),
                "mh5_2021": j.get("mh5_2021"),
                "mh5_2022": j.get("mh5_2022"),
            }
        )
    return {
        "source_note": (
            "Lista COMPÓS — Revistas da Área (Google Scholar: Índice H e mediana h5, 2021 e 2022)"
        ),
        "source_url": "https://compos.org.br/publicacoes/revistas-da-area/",
        "metric_years": [2021, 2022],
        "preferred_h_year": 2022,
        "journals": entries,
    }


def merge_catalogs(
    existing_path: Path,
    compos_journals: list[dict],
    tpl_rows: list[dict],
) -> dict:
    """Merge COMPÓS (by title) + template ISSNs into main snapshot."""
    if existing_path.is_file():
        base = json.loads(existing_path.read_text(encoding="utf-8"))
        merged: dict[str, dict] = {}
        for row in base.get("journals") or []:
            if not isinstance(row, dict):
                continue
            key = normalize_issn(row.get("issn")) or normalize_title(row.get("titulo"))
            if key:
                merged[key] = dict(row)
    else:
        merged = {}

    by_title = {normalize_title(j["titulo"]): j for j in compos_journals}

    for tpl in tpl_rows:
        hit = match_compos(tpl.get("nome") or "", by_title)
        if not hit:
            continue
        h = choose_h(hit)
        if h is None:
            continue
        issn = normalize_issn(tpl.get("issn"))
        titulo = (tpl.get("nome") or "").strip()
        entry = {
            "titulo": titulo,
            "issn": issn or None,
            "h_index": h,
            "h_source": "compos_google_scholar",
            "h_year_used": 2022 if hit.get("h_2022") is not None else 2021,
        }
        key = issn or normalize_title(titulo)
        if key:
            merged[key] = entry

    for j in compos_journals:
        h = choose_h(j)
        if h is None:
            continue
        titulo_key = normalize_title(j["titulo"])
        if not titulo_key:
            continue
        if titulo_key not in {normalize_title(m.get("titulo")) for m in merged.values()}:
            merged[titulo_key] = {
                "titulo": j["titulo"],
                "issn": None,
                "h_index": h,
                "h_source": "compos_google_scholar",
                "h_year_used": 2022 if j.get("h_2022") is not None else 2021,
            }

    return {
        "source_note": (
            "Catálogo unificado: OpenAlex (CSV legado) + COMPÓS Google Scholar 2021/2022"
        ),
        "source_compos_url": "https://compos.org.br/publicacoes/revistas-da-area/",
        "journals": sorted(
            merged.values(),
            key=lambda r: (normalize_title(r.get("titulo")) or ""),
        ),
    }


def main() -> None:
    html_path = Path(
        r"c:\Users\LUCAS\Downloads\Revistas da Área – COMPÓS.html"
    )
    compos = parse_compos_html(html_path)
    by_norm = {normalize_title(j["titulo"]): j for j in compos}

    tpl_path = root / "revistas_hindex_template.csv"
    tpl_rows = list(csv.DictReader(tpl_path.open(encoding="utf-8-sig")))

    matched = sum(1 for r in tpl_rows if match_compos(r.get("nome") or "", by_norm))
    filled = 0
    out_rows = []
    for row in tpl_rows:
        hit = match_compos(row.get("nome") or "", by_norm)
        extra: dict = {}
        if hit:
            h = choose_h(hit)
            if h is not None:
                row = {**row, "h_index": str(int(h) if h == int(h) else h)}
                filled += 1
            extra = {
                "h_2021": hit.get("h_2021") if hit.get("h_2021") is not None else "",
                "h_2022": hit.get("h_2022") if hit.get("h_2022") is not None else "",
                "fonte": "compos.org.br (Google Scholar 2021/2022)",
            }
        out_rows.append({**row, **extra})

    data_dir = root / "data" / "journal_hindex"
    data_dir.mkdir(parents=True, exist_ok=True)

    compos_json_path = data_dir / "compos-revistas-area.json"
    compos_json_path.write_text(
        json.dumps(build_compos_json(compos), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    out_csv = data_dir / "revistas-compos-hindex.csv"
    fieldnames = ["nome", "issn", "qualis", "h_index", "h_2021", "h_2022", "fonte"]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    merged_path = data_dir / "revistas-hindex-comunicacao.json"
    merged = merge_catalogs(merged_path, compos, tpl_rows)
    merged_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    has21 = sum(1 for j in compos if j["h_2021"] is not None)
    has22 = sum(1 for j in compos if j["h_2022"] is not None)
    na_both = sum(1 for j in compos if j["h_2021"] is None and j["h_2022"] is None)

    print(f"COMPOS HTML (rawJournalsData): {len(compos)} revistas")
    print(f"  Com H 2021: {has21} | Com H 2022: {has22} | Sem H: {na_both}")
    print(f"Template PPG: {len(tpl_rows)} linhas")
    print(f"  Match COMPOS: {matched} | h_index preenchido: {filled}")
    print(f"  JSON COMPOS: {compos_json_path}")
    print(f"  CSV merge: {out_csv}")
    print(f"  JSON unificado: {merged_path} ({len(merged['journals'])} entradas)")


if __name__ == "__main__":
    main()
