"""Métricas de perfil Google Acadêmico (autor) e citações por produção

Revision ID: 007_scholar_profile
Revises: 006_scholar_metrics
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_scholar_profile"
down_revision: Union[str, None] = "006_scholar_metrics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "producoes",
        sa.Column("scholar_citations", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_producoes_scholar_citations",
        "producoes",
        ["scholar_citations"],
    )

    op.add_column(
        "professores",
        sa.Column("scholar_user_id", sa.String(), nullable=True),
    )
    op.add_column(
        "professores",
        sa.Column("scholar_citations_total", sa.Integer(), nullable=True),
    )
    op.add_column(
        "professores",
        sa.Column("scholar_h_index", sa.Integer(), nullable=True),
    )
    op.add_column(
        "professores",
        sa.Column("scholar_i10_index", sa.Integer(), nullable=True),
    )
    op.add_column(
        "professores",
        sa.Column("scholar_metrics_since_year", sa.Integer(), nullable=True),
    )
    op.add_column(
        "professores",
        sa.Column("scholar_profile_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_professores_scholar_user_id",
        "professores",
        ["scholar_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_professores_scholar_user_id", table_name="professores")
    op.drop_column("professores", "scholar_profile_synced_at")
    op.drop_column("professores", "scholar_metrics_since_year")
    op.drop_column("professores", "scholar_i10_index")
    op.drop_column("professores", "scholar_h_index")
    op.drop_column("professores", "scholar_citations_total")
    op.drop_column("professores", "scholar_user_id")

    op.drop_index("ix_producoes_scholar_citations", table_name="producoes")
    op.drop_column("producoes", "scholar_citations")
