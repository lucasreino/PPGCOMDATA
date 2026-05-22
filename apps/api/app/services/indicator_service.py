"""Camada de indicadores consolidados para o Dossiê APCN / Proposta de Doutorado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from sqlmodel import Session, select

from app.models.core import Professor, LinhaPesquisa
from app.models.data import (
    Projeto,
    Evento,
    Producao,
    Financiamento,
    AlertaLacuna,
    Orientacao,
    FormacaoAcademica,
    Banca,
    ProducaoTecnica,
    PremioTitulo,
    GrupoPesquisaDocente,
    RelatorioProjeto,
    EventoInstitucional,
    Egresso,
    ProcessoSeletivo,
)
from app.services.analytics_sql import build_analytics_stats_sql
from app.services.proposal_lacuna_service import merge_gaps_with_db
from app.models.enums import (
    StatusValidacao,
    StatusOrientacao,
    TipoProjeto,
    EscopoEvento,
)


@dataclass
class IndicatorFilters:
    professor_id: Optional[str] = None
    linha_pesquisa_id: Optional[str] = None
    ano_inicio: Optional[int] = None
    ano_fim: Optional[int] = None
    apenas_validados: bool = False

    def query_params(self) -> Dict[str, Any]:
        return {
            "professor_id": self.professor_id,
            "linha_pesquisa_id": self.linha_pesquisa_id,
            "ano_inicio": self.ano_inicio,
            "ano_fim": self.ano_fim,
            "apenas_validados": self.apenas_validados,
        }


VALIDATED = (StatusValidacao.CONFIRMADO, StatusValidacao.EDITADO)

PRODUCAO_TIPOS = {
    "artigo": "artigos",
    "livro": "livros",
    "capitulo": "capitulos",
    "capítulo": "capitulos",
    "anais": "anais",
    "trabalho_em_evento": "anais",
    "apresentacao": "apresentacoes",
    "apresentação": "apresentacoes",
}


def _enum_val(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _norm_tipo_producao(tipo: str) -> str:
    t = (tipo or "").lower().strip()
    return PRODUCAO_TIPOS.get(t, "outras")


class IndicatorService:
    def __init__(self, session: Session, filters: Optional[IndicatorFilters] = None):
        self.session = session
        self.filters = filters or IndicatorFilters()
        self._prof_ids: Optional[List[str]] = None
        self._resolve_professor_scope()

    def _resolve_professor_scope(self) -> None:
        f = self.filters
        if f.professor_id:
            self._prof_ids = [f.professor_id]
            return
        if f.linha_pesquisa_id:
            stmt = select(Professor.id).where(
                Professor.linha_pesquisa_id == f.linha_pesquisa_id
            )
            self._prof_ids = list(self.session.exec(stmt).all())
            return
        self._prof_ids = None

    def _apply_prof_filter(self, stmt, model):
        if self.filters.professor_id:
            return stmt.where(model.professor_id == self.filters.professor_id)
        if self._prof_ids is not None:
            if not self._prof_ids:
                return stmt.where(model.professor_id == "__none__")
            return stmt.where(model.professor_id.in_(self._prof_ids))
        return stmt

    def _apply_validacao(self, stmt, model):
        if self.filters.apenas_validados:
            return stmt.where(model.status_validacao.in_(VALIDATED))
        return stmt

    def _fetch(self, model: Type, year_field: Optional[str] = None) -> list:
        stmt = select(model)
        stmt = self._apply_prof_filter(stmt, model)
        if hasattr(model, "status_validacao"):
            stmt = self._apply_validacao(stmt, model)
        f = self.filters
        if year_field and f.ano_inicio is not None:
            col = getattr(model, year_field)
            stmt = stmt.where(col >= f.ano_inicio)
        if year_field and f.ano_fim is not None:
            col = getattr(model, year_field)
            stmt = stmt.where(col <= f.ano_fim)
        return list(self.session.exec(stmt).all())

    def _professores(self) -> List[Professor]:
        stmt = select(Professor)
        if self.filters.professor_id:
            stmt = stmt.where(Professor.id == self.filters.professor_id)
        elif self._prof_ids is not None:
            if not self._prof_ids:
                return []
            stmt = stmt.where(Professor.id.in_(self._prof_ids))
        return list(self.session.exec(stmt).all())

    def _linha_nome(self, prof: Professor) -> str:
        if not prof.linha_pesquisa_id:
            return "Sem linha"
        linha = self.session.get(LinhaPesquisa, prof.linha_pesquisa_id)
        return linha.nome if linha else "Sem linha"

    def _empty_overview(self) -> Dict[str, Any]:
        return {
            "total_docentes": 0,
            "total_producoes": 0,
            "total_projetos": 0,
            "total_eventos": 0,
            "total_financiamentos": 0,
            "total_lacunas": 0,
            "lacunas_pendentes": 0,
            "fomento_total": {"solicitado": 0.0, "aprovado": 0.0, "executado": 0.0},
            "validacao_pendentes": 0,
            "total_orientacoes": 0,
            "modulos_disponiveis": {
                "producao": False,
                "projetos": False,
                "financiamento": False,
                "eventos": False,
                "egressos": False,
                "selecao": False,
            },
            "filtros": self.filters.query_params(),
        }

    def get_overview_indicators(self) -> Dict[str, Any]:
        if self._prof_ids is not None and not self._prof_ids:
            return self._empty_overview()

        profs = self._professores()
        producoes = self._fetch(Producao, "ano")
        projetos = self._fetch(Projeto, "ano_inicio")
        eventos = self._fetch(Evento, "ano")
        financiamentos = self._fetch(Financiamento, "ano")
        lacunas = self._fetch_lacunas()
        orientacoes = self._fetch(Orientacao)

        fomento = {"solicitado": 0.0, "aprovado": 0.0, "executado": 0.0}
        for fin in financiamentos:
            fomento["solicitado"] += fin.valor_solicitado or 0.0
            fomento["aprovado"] += fin.valor_aprovado or 0.0
            fomento["executado"] += fin.valor_executado or 0.0
        fomento = {k: round(v, 2) for k, v in fomento.items()}

        pendentes_val = 0
        for model in (
            Projeto,
            Evento,
            Producao,
            Financiamento,
            Orientacao,
            FormacaoAcademica,
            Banca,
            ProducaoTecnica,
            PremioTitulo,
            GrupoPesquisaDocente,
        ):
            stmt = select(model).where(model.status_validacao == StatusValidacao.PENDENTE)
            stmt = self._apply_prof_filter(stmt, model)
            pendentes_val += len(self.session.exec(stmt).all())

        return {
            "total_docentes": len(profs),
            "total_producoes": len(producoes) + len(self._fetch(ProducaoTecnica)),
            "total_projetos": len(projetos),
            "total_eventos": len(eventos),
            "total_financiamentos": len(financiamentos),
            "total_lacunas": len(lacunas),
            "lacunas_pendentes": sum(1 for l in lacunas if not l.resolvido),
            "fomento_total": fomento,
            "validacao_pendentes": pendentes_val,
            "total_orientacoes": len(orientacoes),
            "orientacoes_concluidas": sum(
                1 for o in orientacoes if o.status == StatusOrientacao.CONCLUIDA
            ),
            "modulos_disponiveis": {
                "producao": True,
                "projetos": True,
                "financiamento": True,
                "eventos": True,
                "egressos": len(self.session.exec(select(Egresso)).all()) > 0,
                "selecao": len(self.session.exec(select(ProcessoSeletivo)).all()) > 0,
            },
            "demanda": self.get_selection_indicators(),
            "egressos_resumo": self.get_egress_indicators(),
            "filtros": self.filters.query_params(),
        }

    def _fetch_lacunas(self) -> List[AlertaLacuna]:
        stmt = select(AlertaLacuna)
        return list(self.session.exec(self._apply_prof_filter(stmt, AlertaLacuna)).all())

    def get_production_indicators(self) -> Dict[str, Any]:
        if self._prof_ids is not None and not self._prof_ids:
            return self._empty_production()

        producoes = self._fetch(Producao, "ano")
        tecnicas = self._fetch(ProducaoTecnica)
        profs = {p.id: p for p in self._professores()}

        totals = {
            "artigos": 0,
            "livros": 0,
            "capitulos": 0,
            "anais": 0,
            "apresentacoes": 0,
            "producao_tecnica": len(tecnicas),
            "outras": 0,
            "total": len(producoes) + len(tecnicas),
        }
        por_tipo: Dict[str, int] = {}
        por_ano: Dict[str, int] = {}
        por_docente: Dict[str, int] = {}
        por_linha: Dict[str, int] = {}
        tabela_docente: List[Dict[str, Any]] = []

        por_docente_detalhe: Dict[str, Dict[str, int]] = {}

        for p in producoes:
            cat = _norm_tipo_producao(p.tipo)
            totals[cat] = totals.get(cat, 0) + 1
            por_tipo[p.tipo] = por_tipo.get(p.tipo, 0) + 1
            if p.ano:
                por_ano[str(p.ano)] = por_ano.get(str(p.ano), 0) + 1
            nome = profs[p.professor_id].nome_completo if p.professor_id in profs else "?"
            por_docente[nome] = por_docente.get(nome, 0) + 1
            linha = self._linha_nome(profs[p.professor_id]) if p.professor_id in profs else "?"
            por_linha[linha] = por_linha.get(linha, 0) + 1

            det = por_docente_detalhe.setdefault(
                p.professor_id,
                {
                    "artigos": 0,
                    "livros": 0,
                    "capitulos": 0,
                    "anais": 0,
                    "apresentacoes": 0,
                    "producao_tecnica": 0,
                    "outras": 0,
                    "pendentes": 0,
                },
            )
            det[cat] = det.get(cat, 0) + 1
            if p.status_validacao == StatusValidacao.PENDENTE:
                det["pendentes"] += 1

        for t in tecnicas:
            if t.professor_id in profs:
                det = por_docente_detalhe.setdefault(
                    t.professor_id,
                    {
                        "artigos": 0,
                        "livros": 0,
                        "capitulos": 0,
                        "anais": 0,
                        "apresentacoes": 0,
                        "producao_tecnica": 0,
                        "outras": 0,
                        "pendentes": 0,
                    },
                )
                det["producao_tecnica"] += 1

        for prof in profs.values():
            det = por_docente_detalhe.get(
                prof.id,
                {
                    "artigos": 0,
                    "livros": 0,
                    "capitulos": 0,
                    "anais": 0,
                    "apresentacoes": 0,
                    "producao_tecnica": 0,
                    "outras": 0,
                    "pendentes": 0,
                },
            )
            total = sum(
                det[k]
                for k in (
                    "artigos",
                    "livros",
                    "capitulos",
                    "anais",
                    "apresentacoes",
                    "producao_tecnica",
                    "outras",
                )
            )
            tabela_docente.append(
                {
                    "professor_id": prof.id,
                    "docente": prof.nome_completo,
                    "linha": self._linha_nome(prof),
                    "artigos": det["artigos"],
                    "livros": det["livros"],
                    "capitulos": det["capitulos"],
                    "anais": det["anais"],
                    "producao_tecnica": det["producao_tecnica"],
                    "apresentacoes": det["apresentacoes"],
                    "total": total,
                    "pendencias": det["pendentes"],
                }
            )

        tabela_docente.sort(key=lambda x: x["total"], reverse=True)

        producao_linha_tipo: Dict[str, Dict[str, int]] = {}
        for p in producoes:
            if p.professor_id not in profs:
                continue
            linha = self._linha_nome(profs[p.professor_id])
            cat = _norm_tipo_producao(p.tipo)
            if linha not in producao_linha_tipo:
                producao_linha_tipo[linha] = {}
            producao_linha_tipo[linha][cat] = producao_linha_tipo[linha].get(cat, 0) + 1

        return {
            "totais": totals,
            "producao_por_tipo": por_tipo,
            "producao_por_ano": dict(sorted(por_ano.items())),
            "producao_por_docente": por_docente,
            "producao_por_linha": por_linha,
            "producao_por_linha_e_tipo": producao_linha_tipo,
            "tabela_por_docente": tabela_docente,
            "ranking_artigos": sorted(
                tabela_docente, key=lambda x: x["artigos"], reverse=True
            )[:10],
            "filtros": self.filters.query_params(),
        }

    def _empty_production(self) -> Dict[str, Any]:
        return {
            "totais": {
                "artigos": 0,
                "livros": 0,
                "capitulos": 0,
                "anais": 0,
                "apresentacoes": 0,
                "producao_tecnica": 0,
                "outras": 0,
                "total": 0,
            },
            "producao_por_tipo": {},
            "producao_por_ano": {},
            "producao_por_docente": {},
            "producao_por_linha": {},
            "tabela_por_docente": [],
            "ranking_artigos": [],
            "filtros": self.filters.query_params(),
        }

    def get_project_indicators(self) -> Dict[str, Any]:
        if self._prof_ids is not None and not self._prof_ids:
            return self._empty_projects()

        projetos = self._fetch(Projeto, "ano_inicio")
        relatorios = self._fetch_relatorios()
        profs = {p.id: p for p in self._professores()}

        pesquisa = sum(1 for p in projetos if p.tipo == TipoProjeto.PESQUISA)
        extensao = sum(1 for p in projetos if p.tipo == TipoProjeto.EXTENSAO)
        com_fin = sum(1 for p in projetos if p.financiamento_mencionado)
        sem_fin = len(projetos) - com_fin

        por_docente: Dict[str, int] = {}
        por_linha: Dict[str, int] = {}
        por_ano: Dict[str, int] = {}
        por_tipo: Dict[str, int] = {}
        tabela: List[Dict[str, Any]] = []

        pesquisa_extensao_por_ano: Dict[str, Dict[str, int]] = {}
        impacto_regional = 0

        for pr in projetos:
            nome = profs[pr.professor_id].nome_completo if pr.professor_id in profs else "?"
            por_docente[nome] = por_docente.get(nome, 0) + 1
            linha = self._linha_nome(profs[pr.professor_id]) if pr.professor_id in profs else "?"
            por_linha[linha] = por_linha.get(linha, 0) + 1
            if pr.ano_inicio:
                ano = str(pr.ano_inicio)
                por_ano[ano] = por_ano.get(ano, 0) + 1
                if ano not in pesquisa_extensao_por_ano:
                    pesquisa_extensao_por_ano[ano] = {"pesquisa": 0, "extensao": 0}
                key = "pesquisa" if pr.tipo == TipoProjeto.PESQUISA else "extensao"
                pesquisa_extensao_por_ano[ano][key] = pesquisa_extensao_por_ano[ano].get(key, 0) + 1
            tipo = _enum_val(pr.tipo)
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
            tabela.append(
                {
                    "titulo": pr.titulo,
                    "docente": nome,
                    "linha": linha,
                    "tipo": tipo,
                    "ano": pr.ano_inicio,
                    "financiamento": "Sim" if pr.financiamento_mencionado else "Não",
                    "agencia": pr.agencia_fomento,
                    "status_validacao": _enum_val(pr.status_validacao),
                    "origem": "lattes",
                }
            )

        por_tema: Dict[str, int] = {}
        por_publico: Dict[str, int] = {}
        por_territorio: Dict[str, int] = {}
        tabela_relatorios: List[Dict[str, Any]] = []

        for rel in relatorios:
            nome = profs[rel.professor_id].nome_completo if rel.professor_id in profs else "?"
            linha = self._linha_nome(profs[rel.professor_id]) if rel.professor_id in profs else "?"
            if rel.tema_principal:
                por_tema[rel.tema_principal] = por_tema.get(rel.tema_principal, 0) + 1
            if rel.publico_atendido:
                por_publico[rel.publico_atendido] = por_publico.get(rel.publico_atendido, 0) + 1
            if rel.territorio_impactado:
                por_territorio[rel.territorio_impactado] = por_territorio.get(
                    rel.territorio_impactado, 0
                ) + 1
            if rel.tipo_impacto and _enum_val(rel.tipo_impacto) in ("regional", "local"):
                impacto_regional += 1
            tabela_relatorios.append(
                {
                    "titulo": rel.titulo,
                    "docente": nome,
                    "linha": linha,
                    "tipo": _enum_val(rel.tipo),
                    "tema": rel.tema_principal,
                    "publico": rel.publico_atendido,
                    "territorio": rel.territorio_impactado,
                    "financiamento": "Sim"
                    if rel.possui_financiamento_confirmado or rel.houve_financiamento
                    else "Não",
                    "produto": rel.produto_gerado,
                    "tipo_impacto": _enum_val(rel.tipo_impacto) if rel.tipo_impacto else None,
                    "origem": "relatorio",
                }
            )

        return {
            "total_projetos_pesquisa": pesquisa,
            "total_projetos_extensao": extensao,
            "projetos_com_financiamento": com_fin,
            "projetos_sem_financiamento": sem_fin,
            "projetos_impacto_regional": impacto_regional,
            "total_relatorios_complementares": len(relatorios),
            "projetos_por_docente": por_docente,
            "projetos_por_linha": por_linha,
            "projetos_por_ano": dict(sorted(por_ano.items())),
            "projetos_por_tipo": por_tipo,
            "pesquisa_extensao_por_ano": pesquisa_extensao_por_ano,
            "projetos_por_tema": por_tema,
            "projetos_por_publico": por_publico,
            "projetos_por_territorio": por_territorio,
            "tabela": tabela,
            "tabela_relatorios": tabela_relatorios,
            "filtros": self.filters.query_params(),
        }

    def _fetch_relatorios(self) -> List[RelatorioProjeto]:
        stmt = select(RelatorioProjeto)
        stmt = self._apply_prof_filter(stmt, RelatorioProjeto)
        return list(self.session.exec(stmt).all())

    def _empty_projects(self) -> Dict[str, Any]:
        return {
            "total_projetos_pesquisa": 0,
            "total_projetos_extensao": 0,
            "projetos_com_financiamento": 0,
            "projetos_sem_financiamento": 0,
            "total_relatorios_complementares": 0,
            "projetos_por_docente": {},
            "projetos_por_linha": {},
            "projetos_por_ano": {},
            "projetos_por_tipo": {},
            "pesquisa_extensao_por_ano": {},
            "projetos_por_tema": {},
            "projetos_por_publico": {},
            "projetos_por_territorio": {},
            "projetos_impacto_regional": 0,
            "tabela": [],
            "tabela_relatorios": [],
            "filtros": self.filters.query_params(),
        }

    def get_financing_indicators(self) -> Dict[str, Any]:
        if self._prof_ids is not None and not self._prof_ids:
            return self._empty_financing()

        financiamentos = self._fetch(Financiamento, "ano")
        projetos = self._fetch(Projeto, "ano_inicio")
        profs = {p.id: p for p in self._professores()}

        mencionados = sum(1 for p in projetos if p.financiamento_mencionado)
        confirmados = len(financiamentos)

        totais = {"solicitado": 0.0, "aprovado": 0.0, "executado": 0.0}
        por_agencia: Dict[str, float] = {}
        por_ano: Dict[str, float] = {}
        por_docente: Dict[str, float] = {}
        por_tipo: Dict[str, int] = {}
        matriz: List[Dict[str, Any]] = []

        for f in financiamentos:
            totais["solicitado"] += f.valor_solicitado or 0.0
            totais["aprovado"] += f.valor_aprovado or 0.0
            totais["executado"] += f.valor_executado or 0.0
            ag = (f.agencia or f.fonte or "Não especificada").strip()
            por_agencia[ag] = por_agencia.get(ag, 0.0) + (f.valor_aprovado or 0.0)
            if f.ano:
                por_ano[str(f.ano)] = por_ano.get(str(f.ano), 0.0) + (f.valor_aprovado or 0.0)
            nome = profs[f.professor_id].nome_completo if f.professor_id in profs else "?"
            por_docente[nome] = por_docente.get(nome, 0.0) + (f.valor_aprovado or 0.0)
            tipo = _enum_val(f.tipo)
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

            vinculo = ""
            if f.projeto_id:
                proj = self.session.get(Projeto, f.projeto_id)
                vinculo = proj.titulo if proj else "Projeto"
            elif f.evento_id:
                ev = self.session.get(Evento, f.evento_id)
                vinculo = ev.nome_evento if ev else "Evento"

            matriz.append(
                {
                    "agencia": ag,
                    "ano": f.ano,
                    "tipo": tipo,
                    "finalidade": tipo,
                    "docente": nome,
                    "vinculo": vinculo,
                    "valor_aprovado": f.valor_aprovado,
                    "valor_executado": f.valor_executado,
                    "status_validacao": _enum_val(f.status_validacao),
                    "origem": "confirmado",
                }
            )

        for p in projetos:
            if p.financiamento_mencionado and not any(
                m.get("vinculo") == p.titulo for m in matriz
            ):
                nome = profs[p.professor_id].nome_completo if p.professor_id in profs else "?"
                matriz.append(
                    {
                        "agencia": p.agencia_fomento or "Mencionado no Lattes",
                        "ano": p.ano_inicio,
                        "tipo": _enum_val(p.tipo),
                        "finalidade": _enum_val(p.tipo),
                        "docente": nome,
                        "vinculo": p.titulo,
                        "valor_aprovado": None,
                        "valor_executado": None,
                        "status_validacao": _enum_val(p.status_validacao),
                        "origem": "mencionado",
                    }
                )

        totais = {k: round(v, 2) for k, v in totais.items()}
        por_agencia = {k: round(v, 2) for k, v in por_agencia.items()}
        por_ano = {k: round(v, 2) for k, v in sorted(por_ano.items())}
        por_docente = {k: round(v, 2) for k, v in por_docente.items()}

        return {
            "total_financiamentos_mencionados": mencionados,
            "total_financiamentos_confirmados": confirmados,
            "valor_total_aprovado": totais["aprovado"],
            "valor_total_executado": totais["executado"],
            "valor_total_solicitado": totais["solicitado"],
            "fomento_total": totais,
            "financiamentos_por_agencia": por_agencia,
            "financiamentos_por_ano": por_ano,
            "financiamentos_por_docente": por_docente,
            "financiamentos_por_tipo": por_tipo,
            "comparativo": {
                "mencionados": mencionados,
                "confirmados": confirmados,
            },
            "matriz_fomento": matriz,
            "filtros": self.filters.query_params(),
        }

    def _empty_financing(self) -> Dict[str, Any]:
        return {
            "total_financiamentos_mencionados": 0,
            "total_financiamentos_confirmados": 0,
            "valor_total_aprovado": 0.0,
            "valor_total_executado": 0.0,
            "valor_total_solicitado": 0.0,
            "fomento_total": {"solicitado": 0.0, "aprovado": 0.0, "executado": 0.0},
            "financiamentos_por_agencia": {},
            "financiamentos_por_ano": {},
            "financiamentos_por_docente": {},
            "financiamentos_por_tipo": {},
            "comparativo": {"mencionados": 0, "confirmados": 0},
            "matriz_fomento": [],
            "filtros": self.filters.query_params(),
        }

    def get_event_indicators(self) -> Dict[str, Any]:
        if self._prof_ids is not None and not self._prof_ids:
            return self._empty_events()

        eventos = self._fetch(Evento, "ano")
        profs = {p.id: p for p in self._professores()}

        organizados = sum(1 for e in eventos if e.eh_organizacao)
        nacionais = sum(1 for e in eventos if e.escopo == EscopoEvento.NACIONAL)
        internacionais = sum(
            1 for e in eventos if e.escopo == EscopoEvento.INTERNACIONAL
        )
        com_fin = sum(1 for e in eventos if e.financiamento_mencionado)

        por_ano: Dict[str, int] = {}
        por_docente: Dict[str, int] = {}
        tabela: List[Dict[str, Any]] = []

        for ev in eventos:
            if ev.ano:
                por_ano[str(ev.ano)] = por_ano.get(str(ev.ano), 0) + 1
            nome = profs[ev.professor_id].nome_completo if ev.professor_id in profs else "?"
            por_docente[nome] = por_docente.get(nome, 0) + 1
            tabela.append(
                {
                    "evento": ev.nome_evento,
                    "ano": ev.ano,
                    "cidade": ev.cidade,
                    "pais": ev.pais,
                    "organizacao": ev.eh_organizacao,
                    "escopo": _enum_val(ev.escopo) if ev.escopo else None,
                    "financiamento": ev.financiamento_mencionado,
                    "docente": nome,
                    "status_validacao": _enum_val(ev.status_validacao),
                }
            )

        instit = list(self.session.exec(select(EventoInstitucional)).all())
        inst_por_ano: Dict[str, int] = {}
        inscritos_por_edicao: Dict[str, int] = {}
        inst_tabela: List[Dict[str, Any]] = []
        total_inscritos = 0
        total_trabalhos = 0
        for ie in instit:
            if ie.ano:
                inst_por_ano[str(ie.ano)] = inst_por_ano.get(str(ie.ano), 0) + 1
            label = f"{ie.nome} ({ie.edicao or ie.ano or '?'})"
            if ie.numero_inscritos:
                inscritos_por_edicao[label] = ie.numero_inscritos
                total_inscritos += ie.numero_inscritos
            if ie.numero_trabalhos:
                total_trabalhos += ie.numero_trabalhos
            inst_tabela.append(
                {
                    "nome": ie.nome,
                    "edicao": ie.edicao,
                    "ano": ie.ano,
                    "tema": ie.tema,
                    "abrangencia": ie.abrangencia,
                    "inscritos": ie.numero_inscritos,
                    "trabalhos": ie.numero_trabalhos,
                    "financiamento": bool(ie.valor_aprovado or ie.agencias_financiadoras),
                    "agencias": ie.agencias_financiadoras,
                    "local": ie.local,
                }
            )

        return {
            "total_eventos": len(eventos) + len(instit),
            "eventos_lattes": len(eventos),
            "eventos_institucionais_count": len(instit),
            "eventos_organizados": organizados,
            "eventos_participacao": len(eventos) - organizados,
            "eventos_nacionais": nacionais,
            "eventos_internacionais": internacionais,
            "eventos_com_financiamento": com_fin,
            "total_inscritos_institucionais": total_inscritos,
            "total_trabalhos_institucionais": total_trabalhos,
            "eventos_por_ano": dict(sorted(por_ano.items())),
            "eventos_institucionais_por_ano": dict(sorted(inst_por_ano.items())),
            "inscritos_por_edicao": inscritos_por_edicao,
            "eventos_por_docente": por_docente,
            "eventos_institucionais_tabela": inst_tabela,
            "tabela": tabela,
            "filtros": self.filters.query_params(),
        }

    def _empty_events(self) -> Dict[str, Any]:
        return {
            "total_eventos": 0,
            "eventos_lattes": 0,
            "eventos_institucionais_count": 0,
            "eventos_organizados": 0,
            "eventos_participacao": 0,
            "eventos_nacionais": 0,
            "eventos_internacionais": 0,
            "eventos_com_financiamento": 0,
            "total_inscritos_institucionais": 0,
            "total_trabalhos_institucionais": 0,
            "eventos_por_ano": {},
            "eventos_institucionais_por_ano": {},
            "inscritos_por_edicao": {},
            "eventos_por_docente": {},
            "eventos_institucionais_tabela": [],
            "tabela": [],
            "filtros": self.filters.query_params(),
        }

    def get_gap_indicators(self) -> Dict[str, Any]:
        if self._prof_ids is not None and not self._prof_ids:
            return self._empty_gaps()

        lacunas = self._fetch_lacunas()
        prof_id = self.filters.professor_id
        merged = merge_gaps_with_db(self.session, lacunas, prof_id)

        por_tipo: Dict[str, int] = {}
        por_gravidade: Dict[str, int] = {}
        por_docente: Dict[str, int] = {}
        por_secao: Dict[str, int] = {}

        for row in merged:
            if row.get("resolvido"):
                continue
            por_tipo[row["tipo_lacuna"]] = por_tipo.get(row["tipo_lacuna"], 0) + 1
            grav = row.get("gravidade", "media")
            por_gravidade[grav] = por_gravidade.get(grav, 0) + 1
            sec = row.get("secao_documento") or "Geral"
            por_secao[sec] = por_secao.get(sec, 0) + 1

        abertas = sum(1 for r in merged if not r.get("resolvido"))
        criticas = sum(
            1 for r in merged if not r.get("resolvido") and r.get("gravidade") == "alta"
        )
        virtuais = sum(1 for r in merged if r.get("virtual"))

        return {
            "total_lacunas": len(merged),
            "lacunas_abertas": abertas,
            "lacunas_criticas": criticas,
            "lacunas_resolvidas": len(merged) - abertas,
            "lacunas_virtuais": virtuais,
            "lacunas_por_tipo": por_tipo,
            "lacunas_por_gravidade": por_gravidade,
            "lacunas_por_secao": por_secao,
            "lacunas_por_docente": por_docente,
            "dados_pendentes_validacao": self._count_validation_pending(),
            "tabela": merged,
            "filtros": self.filters.query_params(),
        }

    def _count_validation_pending(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for key, model in (
            ("projetos", Projeto),
            ("eventos", Evento),
            ("producoes", Producao),
            ("financiamentos", Financiamento),
        ):
            stmt = select(model).where(model.status_validacao == StatusValidacao.PENDENTE)
            stmt = self._apply_prof_filter(stmt, model)
            out[key] = len(self.session.exec(stmt).all())
        return out

    def _empty_gaps(self) -> Dict[str, Any]:
        return {
            "total_lacunas": 0,
            "lacunas_abertas": 0,
            "lacunas_criticas": 0,
            "lacunas_resolvidas": 0,
            "lacunas_por_tipo": {},
            "lacunas_por_gravidade": {},
            "lacunas_por_docente": {},
            "dados_pendentes_validacao": {},
            "tabela": [],
            "filtros": self.filters.query_params(),
        }

    def get_teacher_indicators(self, professor_id: str) -> Dict[str, Any]:
        prof = self.session.get(Professor, professor_id)
        if not prof:
            return {"erro": "Professor não encontrado"}

        svc = IndicatorService(
            self.session,
            IndicatorFilters(
                professor_id=professor_id,
                ano_inicio=self.filters.ano_inicio,
                ano_fim=self.filters.ano_fim,
                apenas_validados=self.filters.apenas_validados,
            ),
        )
        linha = self._linha_nome(prof)
        return {
            "professor": {
                "id": prof.id,
                "nome_completo": prof.nome_completo,
                "linha": linha,
                "tipo_docente": prof.tipo_docente,
                "titulacao_maxima": prof.titulacao_maxima,
            },
            "overview": svc.get_overview_indicators(),
            "producao": svc.get_production_indicators(),
            "projetos": svc.get_project_indicators(),
            "financiamento": svc.get_financing_indicators(),
            "eventos": svc.get_event_indicators(),
            "lacunas": svc.get_gap_indicators(),
        }

    def get_line_indicators(self, linha_pesquisa_id: str) -> Dict[str, Any]:
        linha = self.session.get(LinhaPesquisa, linha_pesquisa_id)
        if not linha:
            return {"erro": "Linha de pesquisa não encontrada"}

        svc = IndicatorService(
            self.session,
            IndicatorFilters(
                linha_pesquisa_id=linha_pesquisa_id,
                ano_inicio=self.filters.ano_inicio,
                ano_fim=self.filters.ano_fim,
                apenas_validados=self.filters.apenas_validados,
            ),
        )
        profs = svc._professores()
        return {
            "linha": {"id": linha.id, "nome": linha.nome, "descricao": linha.descricao},
            "total_docentes": len(profs),
            "docentes": [{"id": p.id, "nome": p.nome_completo} for p in profs],
            "overview": svc.get_overview_indicators(),
            "producao": svc.get_production_indicators(),
            "projetos": svc.get_project_indicators(),
            "financiamento": svc.get_financing_indicators(),
            "eventos": svc.get_event_indicators(),
            "lacunas": svc.get_gap_indicators(),
        }

    def get_corpo_docente_indicators(self) -> Dict[str, Any]:
        profs = self._professores()
        linhas = {l.id: l for l in self.session.exec(select(LinhaPesquisa)).all()}
        tabela = []
        for p in profs:
            linha_nome = linhas[p.linha_pesquisa_id].nome if p.linha_pesquisa_id and p.linha_pesquisa_id in linhas else "Sem linha"
            prod_count = len(
                self.session.exec(
                    select(Producao).where(Producao.professor_id == p.id)
                ).all()
            )
            proj_count = len(
                self.session.exec(
                    select(Projeto).where(Projeto.professor_id == p.id)
                ).all()
            )
            lac_count = len(
                self.session.exec(
                    select(AlertaLacuna).where(
                        AlertaLacuna.professor_id == p.id,
                        AlertaLacuna.resolvido == False,
                    )
                ).all()
            )
            tabela.append(
                {
                    "id": p.id,
                    "nome": p.nome_completo,
                    "linha": linha_nome,
                    "tipo_docente": p.tipo_docente,
                    "titulacao": p.titulacao_maxima,
                    "producoes": prod_count,
                    "projetos": proj_count,
                    "lacunas_abertas": lac_count,
                }
            )
        por_linha: Dict[str, int] = {}
        for row in tabela:
            por_linha[row["linha"]] = por_linha.get(row["linha"], 0) + 1
        return {
            "total_docentes": len(tabela),
            "docentes_por_linha": por_linha,
            "tabela": sorted(tabela, key=lambda x: x["nome"]),
            "filtros": self.filters.query_params(),
        }

    def get_egress_indicators(self) -> Dict[str, Any]:
        egressos = list(self.session.exec(select(Egresso)).all())
        por_ano: Dict[str, int] = {}
        por_setor: Dict[str, int] = {}
        por_estado: Dict[str, int] = {}
        por_genero: Dict[str, int] = {}
        municipios = set()
        tabela: List[Dict[str, Any]] = []

        em_doutorado = 0
        ensino_sup = 0
        publico = 0
        terceiro = 0

        for e in egressos:
            if e.ano_conclusao:
                por_ano[str(e.ano_conclusao)] = por_ano.get(str(e.ano_conclusao), 0) + 1
            if e.setor_atuacao:
                por_setor[e.setor_atuacao] = por_setor.get(e.setor_atuacao, 0) + 1
            if e.estado_atuacao:
                por_estado[e.estado_atuacao] = por_estado.get(e.estado_atuacao, 0) + 1
            if e.genero:
                por_genero[e.genero] = por_genero.get(e.genero, 0) + 1
            if e.cidade_atuacao:
                municipios.add(f"{e.cidade_atuacao}/{e.estado_atuacao or ''}")
            if e.esta_em_doutorado:
                em_doutorado += 1
            setor = (e.setor_atuacao or "").lower()
            if "ensino" in setor or "universidade" in setor:
                ensino_sup += 1
            if "público" in setor or "publico" in setor:
                publico += 1
            if "terceiro" in setor or "ong" in setor:
                terceiro += 1
            tabela.append(
                {
                    "id": str(e.id),
                    "nome": e.nome,
                    "ano_conclusao": e.ano_conclusao,
                    "cidade_origem": e.cidade_origem,
                    "estado_origem": e.estado_origem,
                    "setor_atuacao": e.setor_atuacao,
                    "atividade_atual": e.atividade_atual,
                    "esta_em_doutorado": e.esta_em_doutorado,
                    "instituicao_doutorado": e.instituicao_doutorado,
                    "genero": e.genero,
                }
            )

        return {
            "total_egressos": len(egressos),
            "egressos_em_doutorado": em_doutorado,
            "egressos_ensino_superior": ensino_sup,
            "egressos_setor_publico": publico,
            "egressos_terceiro_setor": terceiro,
            "municipios_alcancados": len(municipios),
            "egressos_por_ano": dict(sorted(por_ano.items())),
            "egressos_por_setor": por_setor,
            "egressos_por_estado": por_estado,
            "perfil_genero": por_genero,
            "tabela": tabela,
            "filtros": self.filters.query_params(),
        }

    def get_selection_indicators(self) -> Dict[str, Any]:
        processos = list(self.session.exec(select(ProcessoSeletivo)).all())
        por_ano: Dict[str, Dict[str, int]] = {}
        total_inscritos = 0
        total_vagas = 0
        total_aprovados = 0
        total_matriculados = 0
        total_cotistas = 0
        relacoes: List[float] = []

        for p in processos:
            total_inscritos += p.inscritos
            total_vagas += p.vagas
            total_aprovados += p.aprovados or 0
            total_matriculados += p.matriculados or 0
            total_cotistas += p.cotistas or 0
            if p.vagas > 0:
                relacoes.append(p.inscritos / p.vagas)
            ano = str(p.ano)
            if ano not in por_ano:
                por_ano[ano] = {"inscritos": 0, "vagas": 0, "aprovados": 0, "matriculados": 0}
            por_ano[ano]["inscritos"] += p.inscritos
            por_ano[ano]["vagas"] += p.vagas
            por_ano[ano]["aprovados"] += p.aprovados or 0
            por_ano[ano]["matriculados"] += p.matriculados or 0

        relacao_media = sum(relacoes) / len(relacoes) if relacoes else 0.0
        taxa_aprovacao = (
            total_aprovados / total_inscritos if total_inscritos else 0.0
        )
        taxa_matricula = (
            total_matriculados / total_aprovados if total_aprovados else 0.0
        )

        return {
            "total_processos": len(processos),
            "total_inscritos": total_inscritos,
            "total_vagas": total_vagas,
            "total_aprovados": total_aprovados,
            "total_matriculados": total_matriculados,
            "total_cotistas": total_cotistas,
            "relacao_media_candidato_vaga": round(relacao_media, 2),
            "taxa_aprovacao": round(taxa_aprovacao, 4),
            "taxa_matricula": round(taxa_matricula, 4),
            "percentual_cotistas": round(
                total_cotistas / total_matriculados if total_matriculados else 0, 4
            ),
            "por_ano": por_ano,
            "tabela": [
                {
                    "id": str(p.id),
                    "ano": p.ano,
                    "nivel": p.nivel,
                    "vagas": p.vagas,
                    "inscritos": p.inscritos,
                    "aprovados": p.aprovados,
                    "matriculados": p.matriculados,
                    "relacao_candidato_vaga": round(p.inscritos / p.vagas, 2)
                    if p.vagas
                    else None,
                }
                for p in processos
            ],
            "filtros": self.filters.query_params(),
        }

    def get_analytics_stats(self) -> Dict[str, Any]:
        """Estatísticas agregadas para /analises/estatisticas (dashboard principal)."""
        if self._prof_ids is not None and not self._prof_ids:
            return {
                "total_producoes": 0,
                "total_projetos": 0,
                "total_eventos": 0,
                "eventos_organizados": 0,
                "eventos_participacao": 0,
                "fomento_total": {"solicitado": 0.0, "aprovado": 0.0, "executado": 0.0},
                "producoes_por_tipo": {},
                "producoes_por_ano": {},
                "projetos_por_situacao": {},
                "fomento_por_agencia": {},
                "lacunas": {"total": 0, "resolvidas": 0, "pendentes": 0, "por_gravidade": {}},
                "total_orientacoes": 0,
                "orientacoes_concluidas": 0,
                "orientacoes_em_andamento": 0,
                "total_bancas": 0,
                "total_formacoes": 0,
                "producoes_por_qualis": {},
                "validacao_pendentes": {},
                "total_producoes_tecnicas": 0,
                "total_premios": 0,
                "total_grupos_pesquisa": 0,
            }

        return build_analytics_stats_sql(
            self.session,
            self._apply_prof_filter,
            self._apply_validacao,
            self.filters.ano_inicio,
            self.filters.ano_fim,
        )

    def get_visao_geral_bundle(self) -> Dict[str, Any]:
        """Overview + demanda + narrativas em uma resposta (aba Visão Geral do dossiê)."""
        from app.services.narrative_service import NarrativeService

        return {
            "overview": self.get_overview_indicators(),
            "demanda": self.get_selection_indicators(),
            "narrativas": NarrativeService(self.session, self.filters).generate_all(),
            "filtros": self.filters.query_params(),
        }
