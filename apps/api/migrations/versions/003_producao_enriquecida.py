"""Enriquece metadados de producoes bibliograficas

Revision ID: 003_producao_enriquecida
Revises: 002_lattes_orientacoes_formacao
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_producao_enriquecida"
down_revision: Union[str, None] = "002_lattes_orientacoes_formacao"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("producoes", sa.Column("autores", sa.String(), nullable=True))
    op.add_column("producoes", sa.Column("qualis", sa.String(), nullable=True))
    op.add_column("producoes", sa.Column("idioma", sa.String(), nullable=True))
    op.add_column("producoes", sa.Column("indexadores", sa.String(), nullable=True))
    op.add_column("producoes", sa.Column("volume", sa.String(), nullable=True))
    op.add_column("producoes", sa.Column("paginas", sa.String(), nullable=True))
    op.add_column("producoes", sa.Column("eh_primeiro_autor", sa.Boolean(), nullable=True))
    op.create_index("ix_producoes_qualis", "producoes", ["qualis"])


def downgrade() -> None:
    op.drop_index("ix_producoes_qualis", table_name="producoes")
    op.drop_column("producoes", "eh_primeiro_autor")
    op.drop_column("producoes", "paginas")
    op.drop_column("producoes", "volume")
    op.drop_column("producoes", "indexadores")
    op.drop_column("producoes", "idioma")
    op.drop_column("producoes", "qualis")
    op.drop_column("producoes", "autores")
