"""Reclassifica projetos Lattes que são, na verdade, vínculos em grupo de pesquisa."""

from __future__ import annotations

from typing import Optional

from sqlmodel import Session, select

from app.models.data import GrupoPesquisaDocente, Projeto
from app.models.enums import FonteDado, PapelGrupoPesquisa, StatusValidacao, TipoProjeto
from app.services.grupo_pesquisa_lattes import (
    extract_codigo_dgp,
    grupo_pesquisa_already_exists,
    is_lattes_projeto_grupo_pesquisa,
)

_OBS_RECLASS = (
    "[reclassificação] Descartado como projeto: vínculo em grupo de pesquisa CNPq."
)


def _projeto_matches_grupo(proj: Projeto) -> bool:
    natureza = proj.tipo.value if proj.tipo == TipoProjeto.OUTRO else ""
    return is_lattes_projeto_grupo_pesquisa(
        proj.titulo,
        natureza,
        proj.descricao or "",
    )


def _ensure_grupo_from_projeto(session: Session, proj: Projeto) -> bool:
    """Cria GrupoPesquisaDocente a partir do projeto se ainda não existir."""
    if grupo_pesquisa_already_exists(session, proj.professor_id, proj.titulo):
        return False
    session.add(
        GrupoPesquisaDocente(
            professor_id=proj.professor_id,
            curriculo_upload_id=proj.curriculo_upload_id,
            nome_grupo=proj.titulo.strip(),
            codigo_dgp=extract_codigo_dgp(proj.titulo, proj.descricao or ""),
            papel=PapelGrupoPesquisa.MEMBRO,
            instituicao=proj.instituicoes,
            fonte_dado=proj.fonte_dado,
            confianca_ia=proj.confianca_ia,
            trecho_original=proj.trecho_original,
            status_validacao=StatusValidacao.PENDENTE,
        )
    )
    return True


def reconcile_projetos_misclassified_as_grupos(
    session: Session,
    professor_id: Optional[str] = None,
    *,
    dry_run: bool = False,
) -> dict[str, int]:
    """
    Para cada Projeto que é grupo CNPq disfarçado de projeto:
    garante registro em grupos_pesquisa_docente e marca o projeto como descartado.
    """
    stmt = select(Projeto).where(Projeto.status_validacao != StatusValidacao.DESCARTADO)
    if professor_id:
        stmt = stmt.where(Projeto.professor_id == professor_id)
    projetos = list(session.exec(stmt).all())

    candidatos = 0
    grupos_criados = 0
    projetos_descartados = 0
    ja_tinham_grupo = 0

    for proj in projetos:
        if not _projeto_matches_grupo(proj):
            continue
        candidatos += 1

        if dry_run:
            if grupo_pesquisa_already_exists(session, proj.professor_id, proj.titulo):
                ja_tinham_grupo += 1
            else:
                grupos_criados += 1
            projetos_descartados += 1
            continue

        if _ensure_grupo_from_projeto(session, proj):
            grupos_criados += 1
        else:
            ja_tinham_grupo += 1

        proj.status_validacao = StatusValidacao.DESCARTADO
        note = _OBS_RECLASS
        if proj.trecho_original and note not in proj.trecho_original:
            proj.trecho_original = f"{proj.trecho_original}\n{note}"
        elif not proj.trecho_original:
            proj.trecho_original = note
        session.add(proj)
        projetos_descartados += 1

    if not dry_run and (grupos_criados or projetos_descartados):
        session.commit()

    return {
        "projetos_analisados": len(projetos),
        "candidatos_grupo": candidatos,
        "grupos_criados": grupos_criados,
        "grupos_ja_existiam": ja_tinham_grupo,
        "projetos_descartados": projetos_descartados,
        "dry_run": dry_run,
    }
