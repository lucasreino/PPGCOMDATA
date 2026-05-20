"""Textos-síntese em português para a proposta de doutorado."""

from __future__ import annotations

from sqlmodel import Session

from app.services.indicator_service import IndicatorFilters, IndicatorService


class NarrativeService:
    def __init__(self, session: Session, filters: IndicatorFilters):
        self.svc = IndicatorService(session, filters)

    def generate_overview_narrative(self) -> str:
        o = self.svc.get_overview_indicators()
        return (
            f"No recorte analisado, o corpo docente do PPGCOM reúne {o['total_docentes']} docentes, "
            f"com {o['total_producoes']} registros de produção intelectual, {o['total_projetos']} projetos "
            f"e {o['total_eventos']} participações ou organizações em eventos. "
            f"O fomento aprovado consolidado alcança R$ {o['fomento_total']['aprovado']:,.2f}, "
            f"com {o['lacunas_pendentes']} lacunas documentais ainda em aberto e "
            f"{o['validacao_pendentes']} itens aguardando validação humana no sistema."
        )

    def generate_production_narrative(self) -> str:
        p = self.svc.get_production_indicators()
        t = p["totais"]
        return (
            f"A produção intelectual mapeada totaliza {t['total']} registros, "
            f"incluindo {t['artigos']} artigos, {t['livros']} livros, {t['capitulos']} capítulos de livros, "
            f"{t['anais']} trabalhos em anais e {t['producao_tecnica']} produções técnicas. "
            f"A distribuição por docente e por ano evidencia a continuidade da atividade de pesquisa "
            f"no período considerado."
        )

    def generate_financing_narrative(self) -> str:
        f = self.svc.get_financing_indicators()
        return (
            f"Foram identificados {f['total_financiamentos_confirmados']} financiamentos confirmados "
            f"e {f['total_financiamentos_mencionados']} menções de fomento em projetos do Lattes. "
            f"Os valores aprovados somam R$ {f['valor_total_aprovado']:,.2f} "
            f"e os executados R$ {f['valor_total_executado']:,.2f}, "
            f"com participação de agências como "
            f"{', '.join(list(f['financiamentos_por_agencia'].keys())[:5]) or 'não especificadas'}."
        )

    def generate_events_narrative(self) -> str:
        e = self.svc.get_event_indicators()
        inst = len(e.get("eventos_institucionais_tabela", []))
        return (
            f"O programa registra {e['total_eventos']} eventos extraídos dos currículos Lattes, "
            f"sendo {e['eventos_organizados']} de organização e {e['eventos_participacao']} de participação. "
            f"Há {e['eventos_nacionais']} com abrangência nacional e {e['eventos_internacionais']} internacionais. "
            f"Complementarmente, {inst} evento(s) institucional(is) do programa (ex.: SIMCOM) "
            f"estão cadastrados para evidências de extensão e divulgação científica."
        )

    def generate_extension_narrative(self) -> str:
        pr = self.svc.get_project_indicators()
        return (
            f"O portfólio de projetos inclui {pr['total_projetos_pesquisa']} projetos de pesquisa "
            f"e {pr['total_projetos_extensao']} de extensão, dos quais {pr['projetos_com_financiamento']} "
            f"indicam financiamento no Lattes. "
            f"Relatórios complementares de impacto social e extensão podem ser vinculados "
            f"({pr['total_relatorios_complementares']} cadastrados) para detalhar público atendido e território."
        )

    def generate_egress_narrative(self) -> str:
        eg = self.svc.get_egress_indicators()
        if eg["total_egressos"] == 0:
            return (
                "Os indicadores de egressos e impacto regional dependem de cadastro ou importação "
                "de dados da coordenação (não extraídos do Lattes)."
            )
        return (
            f"O programa contabiliza {eg['total_egressos']} egressos cadastrados, "
            f"sendo {eg['egressos_em_doutorado']} em doutorado e atuação em "
            f"{eg['municipios_alcancados']} municípios distintos. "
            f"Os setores de atuação mais frequentes concentram-se em "
            f"{', '.join(list(eg.get('egressos_por_setor', {}).keys())[:3]) or 'dados em consolidação'}."
        )

    def generate_gaps_narrative(self) -> str:
        g = self.svc.get_gap_indicators()
        return (
            f"O diagnóstico documental aponta {g['lacunas_abertas']} lacunas em aberto "
            f"({g['lacunas_criticas']} de alta gravidade), incluindo alertas automáticos do pipeline "
            f"e {g.get('lacunas_virtuais', 0)} verificações específicas da proposta APCN. "
            f"A resolução dessas pendências fortalece a consistência das evidências para submissão."
        )

    def generate_all(self) -> dict:
        return {
            "visao_geral": self.generate_overview_narrative(),
            "producao": self.generate_production_narrative(),
            "financiamento": self.generate_financing_narrative(),
            "eventos": self.generate_events_narrative(),
            "extensao": self.generate_extension_narrative(),
            "egressos": self.generate_egress_narrative(),
            "lacunas": self.generate_gaps_narrative(),
        }

    def generate_full_report(self) -> str:
        n = self.generate_all()
        parts = ["# Resumo de Indicadores do PPGCOM\n"]
        labels = {
            "visao_geral": "Visão Geral",
            "producao": "Produção Intelectual",
            "financiamento": "Financiamento",
            "eventos": "Eventos",
            "extensao": "Projetos e Extensão",
            "egressos": "Egressos e Impacto Regional",
            "lacunas": "Lacunas",
        }
        for key, title in labels.items():
            parts.append(f"\n## {title}\n\n{n[key]}\n")
        return "".join(parts)
