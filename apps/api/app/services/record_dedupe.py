"""Detecção e remoção de duplicatas exatas por chave lógica."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable

from sqlmodel import Session, select

from app.models.data import (
    Banca,
    Evento,
    FormacaoAcademica,
    Orientacao,
    PerfilLattes,
    Producao,
    Projeto,
)
from app.models.enums import FonteDado
from app.services.dedupe import normalize_text_key


def _key_parts(*values: Any) -> tuple:
    return tuple(normalize_text_key(str(v) if v is not None else "") for v in values)


DUPLICATE_CHECKS: list[tuple[str, type, Callable[[Any], tuple]]] = [
    ("producoes", Producao, lambda r: _key_parts(r.professor_id, r.tipo, r.titulo, r.ano)),
    ("projetos", Projeto, lambda r: _key_parts(r.professor_id, r.titulo, r.ano_inicio)),
    (
        "orientacoes",
        Orientacao,
        lambda r: _key_parts(
            r.professor_id,
            r.nome_orientando or r.titulo_trabalho,
            r.titulo_trabalho,
            r.ano_conclusao or r.ano_inicio,
        ),
    ),
    (
        "bancas",
        Banca,
        lambda r: _key_parts(
            r.professor_id,
            r.nome_candidato or r.titulo_trabalho,
            r.titulo_trabalho,
            r.ano,
        ),
    ),
    (
        "eventos",
        Evento,
        lambda r: _key_parts(r.professor_id, r.nome_evento, r.ano, r.eh_organizacao),
    ),
    (
        "formacoes",
        FormacaoAcademica,
        lambda r: _key_parts(r.professor_id, r.nivel, r.curso, r.instituicao, r.ano_fim),
    ),
    ("perfis", PerfilLattes, lambda r: _key_parts(r.professor_id, r.curriculo_upload_id)),
]


def find_duplicate_groups(
    rows: Iterable[Any],
    key_fn: Callable[[Any], tuple],
) -> list[tuple[tuple, list[Any]]]:
    buckets: dict[tuple, list[Any]] = defaultdict(list)
    for row in rows:
        buckets[key_fn(row)].append(row)
    return [(k, items) for k, items in buckets.items() if len(items) > 1 and any(k)]


def remove_exact_duplicates(
    session: Session,
    *,
    fonte: FonteDado | None = FonteDado.XML_LATTES,
    dry_run: bool = False,
) -> dict[str, int]:
    """Remove duplicatas exatas, mantendo o registro mais antigo (menor created_at / id)."""
    removed: dict[str, int] = {}

    for label, model, key_fn in DUPLICATE_CHECKS:
        stmt = select(model)
        if fonte is not None and hasattr(model, "fonte_dado"):
            stmt = stmt.where(model.fonte_dado == fonte)  # type: ignore[attr-defined]
        rows = list(session.exec(stmt).all())
        dupes = find_duplicate_groups(rows, key_fn)
        count = 0
        for _key, items in dupes:
            items_sorted = sorted(
                items,
                key=lambda r: (
                    getattr(r, "created_at", None) or "",
                    str(getattr(r, "id", "")),
                ),
            )
            for duplicate in items_sorted[1:]:
                count += 1
                if not dry_run:
                    session.delete(duplicate)
        if count:
            removed[label] = count

    if not dry_run and removed:
        session.commit()
    return removed
