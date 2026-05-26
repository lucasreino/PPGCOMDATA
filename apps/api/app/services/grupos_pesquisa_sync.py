"""Sincroniza vínculos em grupo a partir do cadastro oficial (campo observacoes do docente)."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from sqlmodel import Session, select

from app.models.core import Professor
from app.models.data import GrupoPesquisaDocente
from app.models.enums import (
    ConfiancaIA,
    FonteDado,
    PapelGrupoPesquisa,
    StatusValidacao,
)

_GRUPO_LINE = re.compile(
    r"^Grupo de pesquisa:\s*(.+?)(?:\s*\|\s*|$)",
    re.IGNORECASE | re.MULTILINE,
)
_TEMATICAS_LINE = re.compile(r"^Temáticas:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").lower().strip())


def parse_grupos_from_observacoes(
    observacoes: Optional[str],
) -> List[Tuple[str, Optional[str]]]:
    """Retorna lista (nome_grupo, linha_tematica) a partir de observacoes do docente."""
    if not observacoes or not observacoes.strip():
        return []

    grupo_raw: Optional[str] = None
    m = _GRUPO_LINE.search(observacoes)
    if m:
        grupo_raw = m.group(1).strip()
    else:
        for line in observacoes.splitlines():
            low = line.lower()
            if low.startswith("grupo de pesquisa:"):
                grupo_raw = line.split(":", 1)[1].strip()
                break

    if not grupo_raw:
        return []

    if "|" in grupo_raw:
        grupo_raw = grupo_raw.split("|", 1)[0].strip()

    tematicas: Optional[str] = None
    tm = _TEMATICAS_LINE.search(observacoes)
    if tm:
        tematicas = tm.group(1).strip()

    names = [p.strip() for p in re.split(r"\s*/\s*", grupo_raw) if p.strip()]
    return [(n, tematicas) for n in names]


def sync_grupos_from_observacoes(
    session: Session,
    professor_id: Optional[str] = None,
) -> dict[str, int]:
    """
    Cria registros em grupos_pesquisa_docente quando o docente tem grupo no cadastro
    e ainda não existe vínculo equivalente na tabela.
    """
    stmt = select(Professor)
    if professor_id:
        stmt = stmt.where(Professor.id == professor_id)
    profs = list(session.exec(stmt).all())

    criados = 0
    ignorados = 0
    sem_grupo = 0

    for prof in profs:
        parsed = parse_grupos_from_observacoes(prof.observacoes)
        if not parsed:
            sem_grupo += 1
            continue

        existing = list(
            session.exec(
                select(GrupoPesquisaDocente).where(
                    GrupoPesquisaDocente.professor_id == prof.id
                )
            ).all()
        )
        existing_names = {_norm_name(g.nome_grupo) for g in existing}

        for nome_grupo, linha_tematica in parsed:
            key = _norm_name(nome_grupo)
            if key in existing_names:
                ignorados += 1
                continue
            session.add(
                GrupoPesquisaDocente(
                    professor_id=prof.id,
                    nome_grupo=nome_grupo,
                    linha_tematica=linha_tematica,
                    papel=PapelGrupoPesquisa.MEMBRO,
                    fonte_dado=FonteDado.RELATORIO_MANUAL,
                    confianca_ia=ConfiancaIA.ALTA,
                    status_validacao=StatusValidacao.CONFIRMADO,
                )
            )
            existing_names.add(key)
            criados += 1

    if criados:
        session.commit()
    return {
        "docentes_processados": len(profs),
        "grupos_criados": criados,
        "grupos_ignorados": ignorados,
        "docentes_sem_grupo_em_observacoes": sem_grupo,
    }
