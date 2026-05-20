"""Dossiê APCN: eventos institucionais, egressos, seleção e lacunas estendidas

Revision ID: 005_dossie_apcn
Revises: 004_eventos_premios_grupos
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005_dossie_apcn"
down_revision: Union[str, None] = "004_eventos_premios_grupos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "eventos_institucionais",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("edicao", sa.String(), nullable=True),
        sa.Column("ano", sa.Integer(), nullable=True),
        sa.Column("tema", sa.String(), nullable=True),
        sa.Column("data_inicio", sa.Date(), nullable=True),
        sa.Column("data_fim", sa.Date(), nullable=True),
        sa.Column("local", sa.String(), nullable=True),
        sa.Column("abrangencia", sa.String(), nullable=True),
        sa.Column("numero_inscritos", sa.Integer(), nullable=True),
        sa.Column("numero_trabalhos", sa.Integer(), nullable=True),
        sa.Column("numero_convidados", sa.Integer(), nullable=True),
        sa.Column("agencias_financiadoras", sa.String(), nullable=True),
        sa.Column("valor_aprovado", sa.Float(), nullable=True),
        sa.Column("valor_executado", sa.Float(), nullable=True),
        sa.Column("descricao", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eventos_institucionais_nome", "eventos_institucionais", ["nome"])
    op.create_index("ix_eventos_institucionais_ano", "eventos_institucionais", ["ano"])

    op.create_table(
        "egressos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("ano_ingresso", sa.Integer(), nullable=True),
        sa.Column("ano_conclusao", sa.Integer(), nullable=True),
        sa.Column("cidade_origem", sa.String(), nullable=True),
        sa.Column("estado_origem", sa.String(), nullable=True),
        sa.Column("genero", sa.String(), nullable=True),
        sa.Column("raca_cor", sa.String(), nullable=True),
        sa.Column("escola_origem", sa.String(), nullable=True),
        sa.Column("ingresso_por_cota", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("atividade_atual", sa.String(), nullable=True),
        sa.Column("instituicao_atual", sa.String(), nullable=True),
        sa.Column("cidade_atuacao", sa.String(), nullable=True),
        sa.Column("estado_atuacao", sa.String(), nullable=True),
        sa.Column("setor_atuacao", sa.String(), nullable=True),
        sa.Column("esta_em_doutorado", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("instituicao_doutorado", sa.String(), nullable=True),
        sa.Column("impacto_social_resumo", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_egressos_nome", "egressos", ["nome"])
    op.create_index("ix_egressos_ano_conclusao", "egressos", ["ano_conclusao"])

    op.create_table(
        "processos_seletivos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("nivel", sa.String(), nullable=False),
        sa.Column("vagas", sa.Integer(), nullable=False),
        sa.Column("inscritos", sa.Integer(), nullable=False),
        sa.Column("inscricoes_deferidas", sa.Integer(), nullable=True),
        sa.Column("aprovados", sa.Integer(), nullable=True),
        sa.Column("matriculados", sa.Integer(), nullable=True),
        sa.Column("cotistas", sa.Integer(), nullable=True),
        sa.Column("observacoes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_processos_seletivos_ano", "processos_seletivos", ["ano"])

    for col, typ in (
        ("secao_documento", sa.String()),
        ("entidade_relacionada", sa.String()),
        ("entidade_id", sa.String()),
        ("sugestao_de_correcao", sa.String()),
        ("prioridade", sa.String()),
        ("responsavel", sa.String()),
        ("prazo", sa.Date()),
        ("status_tratamento", sa.String()),
    ):
        op.add_column("alertas_lacunas", sa.Column(col, typ, nullable=True))
    op.execute(
        "UPDATE alertas_lacunas SET status_tratamento = 'resolvida' WHERE resolvido = true"
    )
    op.execute(
        "UPDATE alertas_lacunas SET status_tratamento = 'aberta' WHERE status_tratamento IS NULL"
    )

    for col, typ in (
        ("tema_principal", sa.String()),
        ("publico_atendido", sa.String()),
        ("territorio_impactado", sa.String()),
        ("ods_relacionado", sa.String()),
        ("produto_gerado", sa.String()),
        ("tipo_impacto", sa.String()),
        ("possui_financiamento_confirmado", sa.Boolean()),
    ):
        op.add_column("relatorios_projeto", sa.Column(col, typ, nullable=True))


def downgrade() -> None:
    for col in (
        "tema_principal",
        "publico_atendido",
        "territorio_impactado",
        "ods_relacionado",
        "produto_gerado",
        "tipo_impacto",
        "possui_financiamento_confirmado",
    ):
        op.drop_column("relatorios_projeto", col)
    for col in (
        "secao_documento",
        "entidade_relacionada",
        "entidade_id",
        "sugestao_de_correcao",
        "prioridade",
        "responsavel",
        "prazo",
        "status_tratamento",
    ):
        op.drop_column("alertas_lacunas", col)
    op.drop_table("processos_seletivos")
    op.drop_table("egressos")
    op.drop_table("eventos_institucionais")
