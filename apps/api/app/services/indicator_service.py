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
)
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
                "egressos": False,
                "selecao": False,
            },
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

        return {
            "totais": totals,
            "producao_por_tipo": por_tipo,
            "producao_por_ano": dict(sorted(por_ano.items())),
            "producao_por_docente": por_docente,
            "producao_por_linha": por_linha,
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

        for pr in projetos:
            nome = profs[pr.professor_id].nome_completo if pr.professor_id in profs else "?"
            por_docente[nome] = por_docente.get(nome, 0) + 1
            linha = self._linha_nome(profs[pr.professor_id]) if pr.professor_id in profs else "?"
            por_linha[linha] = por_linha.get(linha, 0) + 1
            if pr.ano_inicio:
                por_ano[str(pr.ano_inicio)] = por_ano.get(str(pr.ano_inicio), 0) + 1
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
                }
            )

        return {
            "total_projetos_pesquisa": pesquisa,
            "total_projetos_extensao": extensao,
            "projetos_com_financiamento": com_fin,
            "projetos_sem_financiamento": sem_fin,
            "total_relatorios_complementares": len(relatorios),
            "projetos_por_docente": por_docente,
            "projetos_por_linha": por_linha,
            "projetos_por_ano": dict(sorted(por_ano.items())),
            "projetos_por_tipo": por_tipo,
            "tabela": tabela,
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
            "tabela": [],
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

        return {
            "total_eventos": len(eventos),
            "eventos_organizados": organizados,
            "eventos_participacao": len(eventos) - organizados,
            "eventos_nacionais": nacionais,
            "eventos_internacionais": internacionais,
            "eventos_com_financiamento": com_fin,
            "eventos_por_ano": dict(sorted(por_ano.items())),
            "eventos_por_docente": por_docente,
            "eventos_institucionais": [],
            "nota": "Eventos institucionais (SIMCOM) serão cadastrados na Etapa 6.",
            "tabela": tabela,
            "filtros": self.filters.query_params(),
        }

    def _empty_events(self) -> Dict[str, Any]:
        return {
            "total_eventos": 0,
            "eventos_organizados": 0,
            "eventos_participacao": 0,
            "eventos_nacionais": 0,
            "eventos_internacionais": 0,
            "eventos_com_financiamento": 0,
            "eventos_por_ano": {},
            "eventos_por_docente": {},
            "eventos_institucionais": [],
            "nota": "Eventos institucionais (SIMCOM) serão cadastrados na Etapa 6.",
            "tabela": [],
            "filtros": self.filters.query_params(),
        }

    def get_gap_indicators(self) -> Dict[str, Any]:
        if self._prof_ids is not None and not self._prof_ids:
            return self._empty_gaps()

        lacunas = self._fetch_lacunas()
        profs = {p.id: p for p in self._professores()}

        por_tipo: Dict[str, int] = {}
        por_gravidade: Dict[str, int] = {}
        por_docente: Dict[str, int] = {}
        tabela: List[Dict[str, Any]] = []

        for l in lacunas:
            por_tipo[l.tipo_lacuna] = por_tipo.get(l.tipo_lacuna, 0) + 1
            grav = _enum_val(l.gravidade)
            por_gravidade[grav] = por_gravidade.get(grav, 0) + 1
            nome = profs[l.professor_id].nome_completo if l.professor_id in profs else "?"
            if not l.resolvido:
                por_docente[nome] = por_docente.get(nome, 0) + 1
            tabela.append(
                {
                    "tipo": l.tipo_lacuna,
                    "descricao": l.descricao,
                    "gravidade": grav,
                    "docente": nome,
                    "resolvido": l.resolvido,
                    "acao_recomendada": l.acao_recomendada,
                }
            )

        abertas = sum(1 for l in lacunas if not l.resolvido)
        criticas = sum(
            1
            for l in lacunas
            if not l.resolvido and _enum_val(l.gravidade) == "alta"
        )

        return {
            "total_lacunas": len(lacunas),
            "lacunas_abertas": abertas,
            "lacunas_criticas": criticas,
            "lacunas_resolvidas": len(lacunas) - abertas,
            "lacunas_por_tipo": por_tipo,
            "lacunas_por_gravidade": por_gravidade,
            "lacunas_por_docente": por_docente,
            "dados_pendentes_validacao": self._count_validation_pending(),
            "tabela": tabela,
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
