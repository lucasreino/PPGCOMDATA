"""Agregações SQL para /analises/estatisticas (evita carregar tabelas inteiras)."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Type

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.data import (
    AlertaLacuna,
    Banca,
    Evento,
    Financiamento,
    FormacaoAcademica,
    GrupoPesquisaDocente,
    Orientacao,
    PremioTitulo,
    Producao,
    ProducaoTecnica,
    Projeto,
)
from app.models.enums import StatusOrientacao, StatusValidacao


def _apply_scope(
    stmt,
    model: Type,
    apply_prof: Callable,
    apply_validacao: Callable,
    year_field: Optional[str],
    ano_inicio: Optional[int],
    ano_fim: Optional[int],
):
    stmt = apply_prof(stmt, model)
    if hasattr(model, "status_validacao"):
        stmt = apply_validacao(stmt, model)
    if year_field and ano_inicio is not None:
        stmt = stmt.where(getattr(model, year_field) >= ano_inicio)
    if year_field and ano_fim is not None:
        stmt = stmt.where(getattr(model, year_field) <= ano_fim)
    return stmt


def count_rows(
    session: Session,
    model: Type,
    apply_prof: Callable,
    apply_validacao: Callable,
    year_field: Optional[str] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
    extra_where: Optional[Callable] = None,
) -> int:
    stmt = select(func.count(model.id))  # type: ignore[attr-defined]
    stmt = _apply_scope(stmt, model, apply_prof, apply_validacao, year_field, ano_inicio, ano_fim)
    if extra_where:
        stmt = extra_where(stmt)
    result = session.exec(stmt).one()
    return int(result or 0)


def group_count(
    session: Session,
    model: Type,
    group_col,
    apply_prof: Callable,
    apply_validacao: Callable,
    year_field: Optional[str] = None,
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
    not_null_col=None,
) -> Dict[str, int]:
    stmt = select(group_col, func.count(model.id))  # type: ignore[attr-defined]
    stmt = _apply_scope(stmt, model, apply_prof, apply_validacao, year_field, ano_inicio, ano_fim)
    if not_null_col is not None:
        stmt = stmt.where(not_null_col.isnot(None))
    stmt = stmt.group_by(group_col)
    out: Dict[str, int] = {}
    for key, cnt in session.exec(stmt).all():
        if key is None:
            continue
        out[str(key)] = int(cnt or 0)
    return out


def build_analytics_stats_sql(
    session: Session,
    apply_prof: Callable,
    apply_validacao: Callable,
    ano_inicio: Optional[int],
    ano_fim: Optional[int],
) -> Dict[str, Any]:
    """Mesmo formato de IndicatorService.get_analytics_stats, via SQL."""

    producoes_por_tipo = group_count(
        session, Producao, Producao.tipo, apply_prof, apply_validacao, "ano", ano_inicio, ano_fim
    )
    producoes_por_ano = group_count(
        session,
        Producao,
        Producao.ano,
        apply_prof,
        apply_validacao,
        "ano",
        ano_inicio,
        ano_fim,
        not_null_col=Producao.ano,
    )
    producoes_por_ano = {str(k): v for k, v in producoes_por_ano.items()}
    producoes_por_qualis_raw = group_count(
        session,
        Producao,
        Producao.qualis,
        apply_prof,
        apply_validacao,
        "ano",
        ano_inicio,
        ano_fim,
        not_null_col=Producao.qualis,
    )
    producoes_por_qualis = {k.upper().strip(): v for k, v in producoes_por_qualis_raw.items()}

    projetos_por_situacao: Dict[str, int] = {}
    stmt_proj = select(Projeto.situacao, func.count(Projeto.id))
    stmt_proj = _apply_scope(
        stmt_proj, Projeto, apply_prof, apply_validacao, "ano_inicio", ano_inicio, ano_fim
    )
    stmt_proj = stmt_proj.group_by(Projeto.situacao)
    for situacao, cnt in session.exec(stmt_proj).all():
        key = situacao or "Não especificada"
        projetos_por_situacao[key] = int(cnt or 0)

    total_eventos = count_rows(
        session, Evento, apply_prof, apply_validacao, "ano", ano_inicio, ano_fim
    )
    eventos_organizados = count_rows(
        session,
        Evento,
        apply_prof,
        apply_validacao,
        "ano",
        ano_inicio,
        ano_fim,
        extra_where=lambda s: s.where(Evento.eh_organizacao == True),  # noqa: E712
    )

    stmt_fin = select(
        func.coalesce(func.sum(Financiamento.valor_solicitado), 0.0),
        func.coalesce(func.sum(Financiamento.valor_aprovado), 0.0),
        func.coalesce(func.sum(Financiamento.valor_executado), 0.0),
    )
    stmt_fin = _apply_scope(
        stmt_fin, Financiamento, apply_prof, apply_validacao, "ano", ano_inicio, ano_fim
    )
    sol, apr, exe = session.exec(stmt_fin).one()
    fomento_total = {
        "solicitado": round(float(sol or 0), 2),
        "aprovado": round(float(apr or 0), 2),
        "executado": round(float(exe or 0), 2),
    }

    fomento_por_agencia: Dict[str, float] = {}
    stmt_ag = select(
        Financiamento.agencia,
        Financiamento.fonte,
        func.coalesce(func.sum(Financiamento.valor_aprovado), 0.0),
    )
    stmt_ag = _apply_scope(
        stmt_ag, Financiamento, apply_prof, apply_validacao, "ano", ano_inicio, ano_fim
    )
    stmt_ag = stmt_ag.group_by(Financiamento.agencia, Financiamento.fonte)
    for agencia, fonte, val in session.exec(stmt_ag).all():
        key = (agencia or fonte or "Outras/Não especificada").upper().strip()
        fomento_por_agencia[key] = round(fomento_por_agencia.get(key, 0.0) + float(val or 0), 2)

    por_gravidade: Dict[str, int] = {}
    stmt_lac = select(AlertaLacuna.gravidade, func.count(AlertaLacuna.id))
    stmt_lac = apply_prof(stmt_lac, AlertaLacuna)
    stmt_lac = stmt_lac.group_by(AlertaLacuna.gravidade)
    for grav, cnt in session.exec(stmt_lac).all():
        g = grav.value if hasattr(grav, "value") else str(grav)
        por_gravidade[g] = int(cnt or 0)

    resolvidas = count_rows(
        session,
        AlertaLacuna,
        apply_prof,
        apply_validacao,
        extra_where=lambda s: s.where(AlertaLacuna.resolvido == True),  # noqa: E712
    )
    total_lacunas = count_rows(session, AlertaLacuna, apply_prof, apply_validacao)

    total_orientacoes = count_rows(session, Orientacao, apply_prof, apply_validacao)
    orientacoes_concluidas = count_rows(
        session,
        Orientacao,
        apply_prof,
        apply_validacao,
        extra_where=lambda s: s.where(Orientacao.status == StatusOrientacao.CONCLUIDA),
    )
    orientacoes_em_andamento = count_rows(
        session,
        Orientacao,
        apply_prof,
        apply_validacao,
        extra_where=lambda s: s.where(Orientacao.status == StatusOrientacao.EM_ANDAMENTO),
    )

    validacao_pendentes: Dict[str, int] = {}
    for key, model in (
        ("projetos", Projeto),
        ("eventos", Evento),
        ("producoes", Producao),
        ("financiamentos", Financiamento),
        ("orientacoes", Orientacao),
        ("formacoes_academicas", FormacaoAcademica),
        ("bancas", Banca),
        ("producoes_tecnicas", ProducaoTecnica),
        ("premios", PremioTitulo),
        ("grupos_pesquisa", GrupoPesquisaDocente),
    ):
        validacao_pendentes[key] = count_rows(
            session,
            model,
            apply_prof,
            apply_validacao,
            extra_where=lambda s, m=model: s.where(m.status_validacao == StatusValidacao.PENDENTE),
        )

    return {
        "total_producoes": count_rows(
            session, Producao, apply_prof, apply_validacao, "ano", ano_inicio, ano_fim
        ),
        "total_projetos": count_rows(
            session, Projeto, apply_prof, apply_validacao, "ano_inicio", ano_inicio, ano_fim
        ),
        "total_eventos": total_eventos,
        "eventos_organizados": eventos_organizados,
        "eventos_participacao": total_eventos - eventos_organizados,
        "total_producoes_tecnicas": count_rows(session, ProducaoTecnica, apply_prof, apply_validacao),
        "total_premios": count_rows(session, PremioTitulo, apply_prof, apply_validacao),
        "total_grupos_pesquisa": count_rows(session, GrupoPesquisaDocente, apply_prof, apply_validacao),
        "fomento_total": fomento_total,
        "producoes_por_tipo": producoes_por_tipo,
        "producoes_por_ano": dict(sorted(producoes_por_ano.items())),
        "projetos_por_situacao": projetos_por_situacao,
        "fomento_por_agencia": fomento_por_agencia,
        "lacunas": {
            "total": total_lacunas,
            "resolvidas": resolvidas,
            "pendentes": total_lacunas - resolvidas,
            "por_gravidade": por_gravidade,
        },
        "total_orientacoes": total_orientacoes,
        "orientacoes_concluidas": orientacoes_concluidas,
        "orientacoes_em_andamento": orientacoes_em_andamento,
        "total_bancas": count_rows(session, Banca, apply_prof, apply_validacao),
        "total_formacoes": count_rows(session, FormacaoAcademica, apply_prof, apply_validacao),
        "producoes_por_qualis": producoes_por_qualis,
        "validacao_pendentes": validacao_pendentes,
    }
