"""Detecta registros duplicados (mesma chave lógica) por professor."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable

from sqlmodel import Session, select

from app.database import engine
from app.models.core import Professor
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


def _find_dupes(
    rows: Iterable[Any],
    key_fn: Callable[[Any], tuple],
) -> list[tuple[tuple, list[Any]]]:
    buckets: dict[tuple, list[Any]] = defaultdict(list)
    for row in rows:
        buckets[key_fn(row)].append(row)
    return [(k, items) for k, items in buckets.items() if len(items) > 1 and any(k)]


def main() -> None:
    checks: list[tuple[str, type, Callable]] = [
        (
            "producoes",
            Producao,
            lambda r: _key_parts(r.professor_id, r.tipo, r.titulo, r.ano),
        ),
        (
            "projetos",
            Projeto,
            lambda r: _key_parts(r.professor_id, r.titulo, r.ano_inicio),
        ),
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
        (
            "perfis",
            PerfilLattes,
            lambda r: _key_parts(r.professor_id, r.curriculo_upload_id),
        ),
    ]

    with Session(engine) as session:
        profs = {p.id: p.nome_completo for p in session.exec(select(Professor)).all()}
        total_groups = 0
        total_extra = 0

        print("Verificação de duplicidade (fonte xml_lattes)\n")
        for label, model, key_fn in checks:
            rows = session.exec(
                select(model).where(model.fonte_dado == FonteDado.XML_LATTES)  # type: ignore
            ).all()
            dupes = _find_dupes(rows, key_fn)
            if not dupes:
                print(f"  {label}: OK (sem duplicatas — {len(rows)} registros)")
                continue

            extra = sum(len(items) - 1 for _, items in dupes)
            total_groups += len(dupes)
            total_extra += extra
            print(f"  {label}: {len(dupes)} grupo(s), {extra} registro(s) redundante(s) ({len(rows)} total)")

            for key, items in sorted(dupes, key=lambda x: -len(x[1]))[:8]:
                pid = items[0].professor_id
                nome = (profs.get(pid) or pid)[:36]
                sample = items[0]
                titulo = getattr(sample, "titulo", None) or getattr(
                    sample, "nome_evento", None
                ) or getattr(sample, "nome_orientando", None) or getattr(
                    sample, "nome_candidato", None
                ) or getattr(sample, "curso", None) or "perfil"
                print(f"    - {nome} | n={len(items)} | {str(titulo)[:70]}")

        print()
        print(f"RESUMO: {total_groups} grupos duplicados, {total_extra} registros a mais que o necessário")
        if total_extra == 0:
            print("Nenhuma duplicidade encontrada.")
        else:
            print("Recomendação: revisar parser XML ou rodar dedupe antes de confirmar.")


if __name__ == "__main__":
    main()
