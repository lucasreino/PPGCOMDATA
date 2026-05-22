"""Ordenação de registros acadêmicos: mais recente primeiro."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, List, Optional, Tuple


def _ts(value: Optional[datetime]) -> float:
    if value is None:
        return 0.0
    try:
        return value.timestamp()
    except (TypeError, ValueError, OSError):
        return 0.0


def _date_ord(value: Optional[date]) -> int:
    if value is None:
        return 0
    return value.year * 10_000 + value.month * 100 + value.day


def _status_value(status: Any) -> str:
    if status is None:
        return ""
    return getattr(status, "value", str(status)).lower()


def entity_recency_key(entity_key: str, obj: Any) -> Tuple[int, float]:
    """Chave de ordenação decrescente: tuplas maiores = mais recentes."""
    created = _ts(getattr(obj, "created_at", None))
    updated = _ts(getattr(obj, "updated_at", None))
    tie_ts = max(created, updated)
    current_year = date.today().year

    if entity_key == "projetos":
        start = int(getattr(obj, "ano_inicio", None) or 0)
        end_raw = getattr(obj, "ano_fim", None)
        if end_raw is not None:
            year = int(end_raw)
        elif start:
            year = current_year
        else:
            year = 0
        primary = max(year, start)
    elif entity_key in ("eventos", "producoes", "producoes_tecnicas", "premios"):
        primary = int(getattr(obj, "ano", None) or 0)
    elif entity_key == "financiamentos":
        vigencia_fim = getattr(obj, "vigencia_fim", None)
        vigencia_inicio = getattr(obj, "vigencia_inicio", None)
        ano = getattr(obj, "ano", None)
        if vigencia_fim is not None:
            primary = _date_ord(vigencia_fim)
        elif ano is not None:
            primary = int(ano)
        elif vigencia_inicio is not None:
            primary = _date_ord(vigencia_inicio)
        else:
            primary = 0
    elif entity_key == "orientacoes":
        conclusao = int(getattr(obj, "ano_conclusao", None) or 0)
        inicio = int(getattr(obj, "ano_inicio", None) or 0)
        primary = max(conclusao, inicio)
        if conclusao == 0 and _status_value(getattr(obj, "status", None)) == "em_andamento":
            primary = max(primary, inicio or current_year)
    elif entity_key == "formacoes_academicas":
        primary = int(
            getattr(obj, "ano_fim", None) or getattr(obj, "ano_inicio", None) or 0
        )
    elif entity_key == "bancas":
        primary = int(getattr(obj, "ano", None) or 0)
    elif entity_key == "perfis_lattes":
        primary = _date_ord(getattr(obj, "data_ultima_atualizacao", None))
    elif entity_key == "lacunas":
        primary = _date_ord(getattr(obj, "prazo", None))
    else:
        primary = 0

    return (primary, tie_ts)


def sort_entities_newest_first(rows: List[Any], entity_key: str) -> List[Any]:
    return sorted(rows, key=lambda row: entity_recency_key(entity_key, row), reverse=True)
