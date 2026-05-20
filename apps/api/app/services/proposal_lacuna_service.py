"""Detecção de lacunas documentais para a proposta APCN (regras sobre o banco)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from app.models.core import Professor
from app.models.data import (
    Projeto,
    Evento,
    Producao,
    Financiamento,
    AlertaLacuna,
    Anexo,
    CurriculoUpload,
    Egresso,
    ProcessoSeletivo,
    EventoInstitucional,
)
from app.models.enums import StatusProcessamento, StatusValidacao, GravidadeLacuna


def _enum_val(v) -> str:
    return v.value if hasattr(v, "value") else str(v)


def scan_proposal_gaps(
    session: Session,
    professor_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retorna lacunas virtuais (não persistidas) para checklist da proposta."""
    gaps: List[Dict[str, Any]] = []

    prof_stmt = select(Professor)
    if professor_id:
        prof_stmt = prof_stmt.where(Professor.id == professor_id)
    professores = list(session.exec(prof_stmt).all())

    for prof in professores:
        pid = str(prof.id)
        nome = prof.nome_completo

        uploads = list(
            session.exec(
                select(CurriculoUpload).where(CurriculoUpload.professor_id == pid)
            ).all()
        )
        ok_upload = any(
            u.status
            in (
                StatusProcessamento.PROCESSADO_COM_SUCESSO,
                StatusProcessamento.PROCESSADO_COM_ALERTAS,
                StatusProcessamento.VALIDADO,
            )
            for u in uploads
        )
        if not ok_upload:
            gaps.append(
                _gap(
                    "docente_sem_lattes",
                    f"Docente sem currículo Lattes processado: {nome}.",
                    "Corpo Docente",
                    "professor",
                    pid,
                    "alta",
                    "Subir e processar PDF do Lattes.",
                )
            )

        projetos = list(
            session.exec(select(Projeto).where(Projeto.professor_id == pid)).all()
        )
        if not projetos:
            gaps.append(
                _gap(
                    "docente_sem_projetos",
                    f"Nenhum projeto registrado para {nome}.",
                    "Projetos e Extensão",
                    "professor",
                    pid,
                    "media",
                    "Verificar extração ou cadastro manual.",
                )
            )
        for pr in projetos:
            if not pr.ano_inicio:
                gaps.append(
                    _gap(
                        "projeto_sem_ano",
                        f"Projeto sem ano de início: \"{pr.titulo[:60]}\" ({nome}).",
                        "Projetos e Extensão",
                        "projeto",
                        str(pr.id),
                        "media",
                        "Informar ano no Lattes ou validar manualmente.",
                    )
                )

        pendentes = len(
            session.exec(
                select(Producao).where(
                    Producao.professor_id == pid,
                    Producao.status_validacao == StatusValidacao.PENDENTE,
                )
            ).all()
        )
        if pendentes >= 5:
            gaps.append(
                _gap(
                    "producao_sem_validacao",
                    f"{pendentes} produções pendentes de validação ({nome}).",
                    "Produção Intelectual",
                    "professor",
                    pid,
                    "media",
                    "Revisar aba de validação do PPGCOMDATA.",
                )
            )

        fins = list(
            session.exec(select(Financiamento).where(Financiamento.professor_id == pid)).all()
        )
        for f in fins:
            if not (f.valor_aprovado or f.valor_executado or f.valor_solicitado):
                gaps.append(
                    _gap(
                        "financiamento_sem_valor",
                        f"Financiamento sem valores registrados ({nome}).",
                        "Financiamento",
                        "financiamento",
                        str(f.id),
                        "alta",
                        "Incluir valores aprovados/executados ou relatório complementar.",
                    )
                )
            anexos = list(
                session.exec(
                    select(Anexo).where(Anexo.financiamento_id == str(f.id))
                ).all()
            )
            if not anexos:
                gaps.append(
                    _gap(
                        "financiamento_sem_comprovante",
                        f"Financiamento sem anexo/comprovante ({nome}).",
                        "Financiamento",
                        "financiamento",
                        str(f.id),
                        "media",
                        "Anexar edital, termo ou relatório de prestação de contas.",
                    )
                )

    for ev in session.exec(select(EventoInstitucional)).all():
        if ev.numero_inscritos is None:
            gaps.append(
                _gap(
                    "evento_sem_numero_inscritos",
                    f"Evento institucional sem número de inscritos: {ev.nome}.",
                    "Eventos",
                    "evento_institucional",
                    str(ev.id),
                    "media",
                    "Preencher dados da edição (coordenação/SIMCOM).",
                )
            )
        if ev.valor_aprovado and not ev.agencias_financiadoras:
            gaps.append(
                _gap(
                    "evento_sem_agencia",
                    f"Evento com valor aprovado mas sem agência: {ev.nome}.",
                    "Eventos",
                    "evento_institucional",
                    str(ev.id),
                    "baixa",
                    "Registrar agências financiadoras.",
                )
            )

    for eg in session.exec(select(Egresso)).all():
        if not eg.atividade_atual and not eg.setor_atuacao:
            gaps.append(
                _gap(
                    "egresso_sem_destino",
                    f"Egresso sem destino profissional: {eg.nome}.",
                    "Egressos e Impacto Regional",
                    "egresso",
                    str(eg.id),
                    "media",
                    "Atualizar cadastro de egresso.",
                )
            )

    for ps in session.exec(select(ProcessoSeletivo)).all():
        if ps.inscritos == 0 or ps.vagas == 0:
            gaps.append(
                _gap(
                    "selecao_sem_numero",
                    f"Processo seletivo {ps.nivel} ({ps.ano}) com inscritos ou vagas zerados.",
                    "Demanda Discente",
                    "processo_seletivo",
                    str(ps.id),
                    "alta",
                    "Conferir dados da secretaria.",
                )
            )

    return gaps


def _gap(
    tipo: str,
    descricao: str,
    secao: str,
    entidade: str,
    entidade_id: str,
    gravidade: str,
    sugestao: str,
) -> Dict[str, Any]:
    return {
        "tipo_lacuna": tipo,
        "descricao": descricao,
        "secao_documento": secao,
        "entidade_relacionada": entidade,
        "entidade_id": entidade_id,
        "gravidade": gravidade,
        "sugestao_de_correcao": sugestao,
        "resolvido": False,
        "virtual": True,
        "status_tratamento": "aberta",
    }


def merge_gaps_with_db(
    session: Session,
    db_lacunas: List[AlertaLacuna],
    professor_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Combina alertas do banco com lacunas virtuais da proposta."""
    rows: List[Dict[str, Any]] = []
    for l in db_lacunas:
        rows.append(
            {
                "id": str(l.id),
                "tipo_lacuna": l.tipo_lacuna,
                "descricao": l.descricao,
                "secao_documento": l.secao_documento,
                "entidade_relacionada": l.entidade_relacionada,
                "entidade_id": l.entidade_id,
                "gravidade": _enum_val(l.gravidade),
                "sugestao_de_correcao": l.sugestao_de_correcao or l.acao_recomendada,
                "prioridade": l.prioridade,
                "responsavel": l.responsavel,
                "prazo": l.prazo.isoformat() if l.prazo else None,
                "resolvido": l.resolvido,
                "status_tratamento": _enum_val(l.status_tratamento) if l.status_tratamento else (
                    "resolvida" if l.resolvido else "aberta"
                ),
                "virtual": False,
            }
        )
    virtual = scan_proposal_gaps(session, professor_id)
    seen = {(r["tipo_lacuna"], r.get("entidade_id")) for r in rows}
    for v in virtual:
        key = (v["tipo_lacuna"], v.get("entidade_id"))
        if key not in seen:
            rows.append(v)
    return rows
