"""Eventos enriquecidos, produção técnica, prêmios e grupos

Revision ID: 004_eventos_premios_grupos
Revises: 003_producao_enriquecida
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_eventos_premios_grupos"
down_revision: Union[str, None] = "003_producao_enriquecida"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("eventos", sa.Column("eh_organizacao", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("eventos", sa.Column("escopo", sa.String(), nullable=True))
    op.add_column("eventos", sa.Column("instituicao_promotora", sa.String(), nullable=True))
    op.create_index("ix_eventos_eh_organizacao", "eventos", ["eh_organizacao"])

    op.create_table(
        "producoes_tecnicas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column("curriculo_upload_id", sa.UUID(), nullable=True),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=True),
        sa.Column("instituicao", sa.String(), nullable=True),
        sa.Column("descricao", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
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

    op.create_table(
        "premios_titulos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column("curriculo_upload_id", sa.UUID(), nullable=True),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=True),
        sa.Column("instituicao_concedente", sa.String(), nullable=True),
        sa.Column("descricao", sa.String(), nullable=True),
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

    op.create_table(
        "grupos_pesquisa_docente",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("professor_id", sa.UUID(), nullable=False),
        sa.Column("curriculo_upload_id", sa.UUID(), nullable=True),
        sa.Column("nome_grupo", sa.String(), nullable=False),
        sa.Column("codigo_dgp", sa.String(), nullable=True),
        sa.Column("papel", sa.String(), nullable=False),
        sa.Column("linha_tematica", sa.String(), nullable=True),
        sa.Column("instituicao", sa.String(), nullable=True),
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


def downgrade() -> None:
    op.drop_table("grupos_pesquisa_docente")
    op.drop_table("premios_titulos")
    op.drop_table("producoes_tecnicas")
    op.drop_index("ix_eventos_eh_organizacao", table_name="eventos")
    op.drop_column("eventos", "instituicao_promotora")
    op.drop_column("eventos", "escopo")
    op.drop_column("eventos", "eh_organizacao")
