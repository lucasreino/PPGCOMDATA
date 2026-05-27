"""Agrupa artigos repetidos entre docentes (mesma obra, coautoria)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.models.data import Producao
from app.services.dedupe import normalize_text_key


def is_artigo_tipo(tipo: Optional[str]) -> bool:
    return (tipo or "").lower().strip() in ("artigo", "artigos")


def artigo_work_key(
    titulo: str,
    ano: Optional[int],
    doi: Optional[str] = None,
) -> str:
    """Chave lógica da obra: DOI quando existir, senão título normalizado + ano."""
    doi_key = normalize_text_key((doi or "").strip())
    if doi_key:
        return f"doi:{doi_key}"
    title_key = normalize_text_key(titulo or "")
    if not title_key:
        return ""
    return f"t:{title_key}|y:{ano or ''}"


def group_artigos_by_work(
    producoes: Iterable[Producao],
) -> Dict[str, List[Producao]]:
    groups: Dict[str, List[Producao]] = defaultdict(list)
    for prod in producoes:
        if not is_artigo_tipo(prod.tipo):
            continue
        key = artigo_work_key(prod.titulo, prod.ano, prod.doi)
        if not key:
            continue
        groups[key].append(prod)
    return dict(groups)


def pick_representative_producao(items: List[Producao]) -> Producao:
    def score(p: Producao) -> tuple:
        has_qualis = 1 if (p.qualis or "").strip() else 0
        has_scholar = 1 if p.scholar_h5_index is not None else 0
        has_journal_h = 1 if p.journal_h_index is not None else 0
        has_citations = 1 if p.scholar_citations is not None else 0
        autores_len = len((p.autores or "").strip())
        return (has_qualis, has_citations, has_scholar, has_journal_h, autores_len)

    return max(items, key=score)


def build_artigo_work_insights(
    groups: Dict[str, List[Producao]],
    prof_names: Dict[str, str],
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Retorna lista de obras únicas e contagem de participações por docente (nome).
    """
    obras: List[Dict[str, Any]] = []
    participacoes_por_docente: Dict[str, int] = defaultdict(int)

    for _key, items in groups.items():
        rep = pick_representative_producao(items)
        docente_ids = sorted({str(p.professor_id) for p in items})
        docentes_nomes = [prof_names.get(pid, "Docente") for pid in docente_ids]
        for nome in docentes_nomes:
            participacoes_por_docente[nome] += 1

        autores_lattes = (rep.autores or "").strip() or None
        obras.append(
            {
                "id": str(rep.id),
                "ids_registros": [str(p.id) for p in items],
                "professor_id": str(rep.professor_id),
                "professor_nome": prof_names.get(str(rep.professor_id), "Docente"),
                "docentes_ppgcom": docentes_nomes,
                "num_docentes_ppgcom": len(docentes_nomes),
                "eh_coautoria": len(docentes_nomes) > 1,
                "titulo": rep.titulo,
                "veiculo": (rep.veiculo or "Revista não informada").strip(),
                "qualis": rep.qualis,
                "scholar_h5_index": rep.scholar_h5_index,
                "scholar_h5_median": rep.scholar_h5_median,
                "scholar_metrics_year": rep.scholar_metrics_year,
                "scholar_citations": rep.scholar_citations,
                "journal_h_index": rep.journal_h_index,
                "ano": rep.ano,
                "doi": rep.doi,
                "autores_lattes": autores_lattes,
            }
        )

    obras.sort(key=lambda a: (a.get("ano") or 0), reverse=True)
    return obras, dict(participacoes_por_docente)
