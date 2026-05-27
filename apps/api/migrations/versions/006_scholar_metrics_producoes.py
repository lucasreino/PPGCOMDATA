"""Google Scholar Metrics (h5) em produções

Revision ID: 006_scholar_metrics
Revises: 005_dossie_apcn
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_scholar_metrics"
down_revision: Union[str, None] = "005_dossie_apcn"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "producoes",
        sa.Column("scholar_h5_index", sa.Integer(), nullable=True),
    )
    op.add_column(
        "producoes",
        sa.Column("scholar_h5_median", sa.Integer(), nullable=True),
    )
    op.add_column(
        "producoes",
        sa.Column("scholar_metrics_year", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_producoes_scholar_h5_index",
        "producoes",
        ["scholar_h5_index"],
    )


def downgrade() -> None:
    op.drop_index("ix_producoes_scholar_h5_index", table_name="producoes")
    op.drop_column("producoes", "scholar_metrics_year")
    op.drop_column("producoes", "scholar_h5_median")
    op.drop_column("producoes", "scholar_h5_index")
