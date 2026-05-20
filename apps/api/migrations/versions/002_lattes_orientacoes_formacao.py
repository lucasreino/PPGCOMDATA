"""Expand Lattes data: formacao, orientacoes, bancas, perfil

Revision ID: 002_lattes_orientacoes_formacao
Revises: 001_initial_schema
Create Date: 2026-05-20 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_lattes_orientacoes_formacao"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("professores", sa.Column("titulacao_maxima", sa.String(), nullable=True))
    op.add_column(
        "professores",
        sa.Column("data_ultima_atualizacao_lattes", sa.Date(), nullable=True),
    )
    op.create_index("ix_professores_titulacao_maxima", "professores", ["titulacao_maxima"])

    op.create_table(
        "formacoes_academicas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column("curriculo_upload_id", sa.UUID(), nullable=True),
        sa.Column("nivel", sa.String(), nullable=False),
        sa.Column("curso", sa.String(), nullable=True),
        sa.Column("instituicao", sa.String(), nullable=True),
        sa.Column("ano_inicio", sa.Integer(), nullable=True),
        sa.Column("ano_fim", sa.Integer(), nullable=True),
        sa.Column("area_conhecimento", sa.String(), nullable=True),
        sa.Column("pais", sa.String(), nullable=True),
        sa.Column("periodo_sanduiche", sa.Boolean(), nullable=False),
        sa.Column("instituicao_exterior", sa.String(), nullable=True),
        sa.Column("fonte_dado", sa.String(), nullable=False),
        sa.Column("confianca_ia", sa.String(), nullable=True),
        sa.Column("trecho_original", sa.String(), nullable=True),
        sa.Column("status_validacao", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["professor_id"], ["professores.id"]),
        sa.ForeignKeyConstraint(["curriculo_upload_id"], ["curriculo_uploads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_formacoes_academicas_id", "formacoes_academicas", ["id"])
    op.create_index(
        "ix_formacoes_academicas_professor_id", "formacoes_academicas", ["professor_id"]
    )
    op.create_index("ix_formacoes_academicas_nivel", "formacoes_academicas", ["nivel"])

    op.create_table(
        "orientacoes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column("curriculo_upload_id", sa.UUID(), nullable=True),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("nome_orientando", sa.String(), nullable=True),
        sa.Column("titulo_trabalho", sa.String(), nullable=True),
        sa.Column("instituicao", sa.String(), nullable=True),
        sa.Column("ano_inicio", sa.Integer(), nullable=True),
        sa.Column("ano_conclusao", sa.Integer(), nullable=True),
        sa.Column("papel", sa.String(), nullable=False),
        sa.Column("fonte_dado", sa.String(), nullable=False),
        sa.Column("confianca_ia", sa.String(), nullable=True),
        sa.Column("trecho_original", sa.String(), nullable=True),
        sa.Column("observacoes", sa.String(), nullable=True),
        sa.Column("status_validacao", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["professor_id"], ["professores.id"]),
        sa.ForeignKeyConstraint(["curriculo_upload_id"], ["curriculo_uploads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orientacoes_id", "orientacoes", ["id"])
    op.create_index("ix_orientacoes_professor_id", "orientacoes", ["professor_id"])
    op.create_index("ix_orientacoes_tipo", "orientacoes", ["tipo"])
    op.create_index("ix_orientacoes_status", "orientacoes", ["status"])

    op.create_table(
        "bancas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column("curriculo_upload_id", sa.UUID(), nullable=True),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("nivel", sa.String(), nullable=False),
        sa.Column("nome_candidato", sa.String(), nullable=True),
        sa.Column("titulo_trabalho", sa.String(), nullable=True),
        sa.Column("instituicao", sa.String(), nullable=True),
        sa.Column("ano", sa.Integer(), nullable=True),
        sa.Column("papel", sa.String(), nullable=False),
        sa.Column("fonte_dado", sa.String(), nullable=False),
        sa.Column("confianca_ia", sa.String(), nullable=True),
        sa.Column("trecho_original", sa.String(), nullable=True),
        sa.Column("observacoes", sa.String(), nullable=True),
        sa.Column("status_validacao", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["professor_id"], ["professores.id"]),
        sa.ForeignKeyConstraint(["curriculo_upload_id"], ["curriculo_uploads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bancas_id", "bancas", ["id"])
    op.create_index("ix_bancas_professor_id", "bancas", ["professor_id"])

    op.create_table(
        "perfis_lattes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column("curriculo_upload_id", sa.UUID(), nullable=True),
        sa.Column("data_ultima_atualizacao", sa.Date(), nullable=True),
        sa.Column("resumo_cv", sa.String(), nullable=True),
        sa.Column("palavras_chave", sa.String(), nullable=True),
        sa.Column("nome_citacao", sa.String(), nullable=True),
        sa.Column("link_orcid", sa.String(), nullable=True),
        sa.Column("fonte_dado", sa.String(), nullable=False),
        sa.Column("confianca_ia", sa.String(), nullable=True),
        sa.Column("trecho_original", sa.String(), nullable=True),
        sa.Column("status_validacao", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["professor_id"], ["professores.id"]),
        sa.ForeignKeyConstraint(["curriculo_upload_id"], ["curriculo_uploads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_perfis_lattes_id", "perfis_lattes", ["id"])
    op.create_index("ix_perfis_lattes_professor_id", "perfis_lattes", ["professor_id"])


def downgrade() -> None:
    op.drop_table("perfis_lattes")
    op.drop_table("bancas")
    op.drop_table("orientacoes")
    op.drop_table("formacoes_academicas")
    op.drop_index("ix_professores_titulacao_maxima", table_name="professores")
    op.drop_column("professores", "data_ultima_atualizacao_lattes")
    op.drop_column("professores", "titulacao_maxima")
