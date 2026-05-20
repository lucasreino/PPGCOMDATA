"""Exportação CSV e Markdown para o Dossiê APCN."""

from __future__ import annotations

import csv
import io
from typing import Any, Dict

from sqlmodel import Session

from app.services.indicator_service import IndicatorFilters, IndicatorService
from app.services.narrative_service import NarrativeService


class ExportService:
    def __init__(self, session: Session, filters: IndicatorFilters):
        self.session = session
        self.filters = filters
        self.indicators = IndicatorService(session, filters)

    def producao_csv(self) -> str:
        data = self.indicators.get_production_indicators()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            [
                "Docente",
                "Linha",
                "Artigos",
                "Livros",
                "Capítulos",
                "Anais",
                "Produção Técnica",
                "Apresentações",
                "Total",
                "Pendências",
            ]
        )
        for row in data.get("tabela_por_docente", []):
            w.writerow(
                [
                    row.get("docente"),
                    row.get("linha"),
                    row.get("artigos"),
                    row.get("livros"),
                    row.get("capitulos"),
                    row.get("anais"),
                    row.get("producao_tecnica"),
                    row.get("apresentacoes", 0),
                    row.get("total"),
                    row.get("pendencias"),
                ]
            )
        return buf.getvalue()

    def financiamento_csv(self) -> str:
        data = self.indicators.get_financing_indicators()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            [
                "Agência",
                "Ano",
                "Tipo",
                "Docente",
                "Vínculo",
                "Origem",
                "Valor Aprovado",
                "Valor Executado",
                "Status",
            ]
        )
        for row in data.get("matriz_fomento", []):
            w.writerow(
                [
                    row.get("agencia"),
                    row.get("ano"),
                    row.get("tipo"),
                    row.get("docente"),
                    row.get("vinculo"),
                    row.get("origem"),
                    row.get("valor_aprovado"),
                    row.get("valor_executado"),
                    row.get("status_validacao"),
                ]
            )
        return buf.getvalue()

    def projetos_csv(self) -> str:
        data = self.indicators.get_project_indicators()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Título", "Docente", "Linha", "Tipo", "Ano", "Financiamento", "Agência", "Status"])
        for row in data.get("tabela", []):
            w.writerow(
                [
                    row.get("titulo"),
                    row.get("docente"),
                    row.get("linha"),
                    row.get("tipo"),
                    row.get("ano"),
                    row.get("financiamento"),
                    row.get("agencia"),
                    row.get("status_validacao"),
                ]
            )
        return buf.getvalue()

    def eventos_csv(self) -> str:
        data = self.indicators.get_event_indicators()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            [
                "Evento",
                "Ano",
                "Cidade",
                "País",
                "Organização",
                "Escopo",
                "Financiamento",
                "Docente",
                "Origem",
            ]
        )
        for row in data.get("tabela", []):
            w.writerow(
                [
                    row.get("evento"),
                    row.get("ano"),
                    row.get("cidade"),
                    row.get("pais"),
                    row.get("organizacao"),
                    row.get("escopo"),
                    row.get("financiamento"),
                    row.get("docente"),
                    "lattes",
                ]
            )
        for row in data.get("eventos_institucionais_tabela", []):
            w.writerow(
                [
                    row.get("nome"),
                    row.get("ano"),
                    row.get("local"),
                    "",
                    "Sim",
                    row.get("abrangencia"),
                    row.get("financiamento"),
                    "",
                    "institucional",
                ]
            )
        return buf.getvalue()

    def lacunas_csv(self) -> str:
        data = self.indicators.get_gap_indicators()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            [
                "Tipo",
                "Descrição",
                "Seção",
                "Entidade",
                "Gravidade",
                "Status",
                "Sugestão",
                "Virtual",
            ]
        )
        for row in data.get("tabela", []):
            w.writerow(
                [
                    row.get("tipo_lacuna") or row.get("tipo"),
                    row.get("descricao"),
                    row.get("secao_documento"),
                    row.get("entidade_relacionada"),
                    row.get("gravidade"),
                    row.get("status_tratamento"),
                    row.get("sugestao_de_correcao"),
                    row.get("virtual"),
                ]
            )
        return buf.getvalue()

    def egressos_csv(self) -> str:
        data = self.indicators.get_egress_indicators()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            [
                "Nome",
                "Ano Conclusão",
                "Cidade Origem",
                "Estado Origem",
                "Setor",
                "Atividade",
                "Doutorado",
                "Instituição Doutorado",
            ]
        )
        for row in data.get("tabela", []):
            w.writerow(
                [
                    row.get("nome"),
                    row.get("ano_conclusao"),
                    row.get("cidade_origem"),
                    row.get("estado_origem"),
                    row.get("setor_atuacao"),
                    row.get("atividade_atual"),
                    row.get("esta_em_doutorado"),
                    row.get("instituicao_doutorado"),
                ]
            )
        return buf.getvalue()

    def resumo_markdown(self) -> str:
        return NarrativeService(self.session, self.filters).generate_full_report()
