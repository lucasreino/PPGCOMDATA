"""H-index de revistas (nível periódico) em producoes

Revision ID: 008_journal_hindex
Revises: 007_scholar_profile
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_journal_hindex"
down_revision: Union[str, None] = "007_scholar_profile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "producoes",
        sa.Column("journal_h_index", sa.Float(), nullable=True),
    )
    op.create_index(
        "ix_producoes_journal_h_index",
        "producoes",
        ["journal_h_index"],
    )


def downgrade() -> None:
    op.drop_index("ix_producoes_journal_h_index", table_name="producoes")
    op.drop_column("producoes", "journal_h_index")
