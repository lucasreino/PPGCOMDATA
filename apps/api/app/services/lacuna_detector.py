"""Rule-based gap detection after AI extraction (no XML required)."""

from typing import List

from app.schemas.ai import AILacunaSchema, AIOrientacaoSchema, AIProducaoSchema
from app.models.enums import GravidadeLacuna, StatusOrientacao


def detect_orientacao_lacunas(orientacoes: List[AIOrientacaoSchema]) -> List[AILacunaSchema]:
    lacunas: List[AILacunaSchema] = []
    current_year = 2026

    for ori in orientacoes:
        if ori.status == StatusOrientacao.EM_ANDAMENTO and not ori.ano_conclusao:
            lacunas.append(
                AILacunaSchema(
                    tipo_lacuna="orientacao_sem_previsao",
                    descricao=(
                        f"Orientação em andamento sem ano previsto de conclusão "
                        f"({ori.nome_orientando or 'orientando não identificado'})."
                    ),
                    gravidade=GravidadeLacuna.MEDIA,
                    acao_recomendada="Atualizar o Lattes com previsão de conclusão.",
                    trecho_original=ori.trecho_original,
                )
            )
        if (
            ori.status == StatusOrientacao.EM_ANDAMENTO
            and ori.ano_inicio
            and current_year - ori.ano_inicio >= 4
        ):
            lacunas.append(
                AILacunaSchema(
                    tipo_lacuna="orientacao_longa",
                    descricao=(
                        f"Orientação em andamento há mais de 4 anos "
                        f"(início {ori.ano_inicio})."
                    ),
                    gravidade=GravidadeLacuna.MEDIA,
                    acao_recomendada="Verificar situação da orientação com o docente.",
                    trecho_original=ori.trecho_original,
                )
            )
        if not ori.nome_orientando and not ori.titulo_trabalho:
            lacunas.append(
                AILacunaSchema(
                    tipo_lacuna="orientacao_incompleta",
                    descricao="Registro de orientação sem nome do orientando nem título do trabalho.",
                    gravidade=GravidadeLacuna.BAIXA,
                    acao_recomendada="Completar dados no Lattes ou validar manualmente.",
                    trecho_original=ori.trecho_original,
                )
            )
    return lacunas


def detect_producao_lacunas(producoes: list[AIProducaoSchema]) -> list[AILacunaSchema]:
    lacunas: list[AILacunaSchema] = []
    current_year = 2026

    for prod in producoes:
        if prod.tipo == "artigo" and prod.ano and prod.ano >= current_year - 3 and not prod.doi:
            lacunas.append(
                AILacunaSchema(
                    tipo_lacuna="artigo_sem_doi",
                    descricao=f"Artigo recente sem DOI: \"{prod.titulo[:80]}\".",
                    gravidade=GravidadeLacuna.BAIXA,
                    acao_recomendada="Incluir DOI no Lattes quando disponível.",
                    trecho_original=prod.trecho_original,
                )
            )
        if prod.tipo == "artigo" and prod.ano and prod.ano >= current_year - 5 and not prod.qualis:
            lacunas.append(
                AILacunaSchema(
                    tipo_lacuna="artigo_sem_qualis",
                    descricao=f"Artigo sem estrato Qualis identificado: \"{prod.titulo[:80]}\".",
                    gravidade=GravidadeLacuna.MEDIA,
                    acao_recomendada="Verificar classificação Qualis do periódico.",
                    trecho_original=prod.trecho_original,
                )
            )
    return lacunas
