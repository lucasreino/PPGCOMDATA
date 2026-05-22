"""Adiciona coluna foto_url em professores. Execute: python -m app.migrate_add_foto_url"""

import os
import sys

from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine


def main() -> None:
    with engine.connect() as conn:
        conn.execute(
            text(
                "ALTER TABLE professores ADD COLUMN IF NOT EXISTS foto_url VARCHAR"
            )
        )
        conn.commit()
    print("Coluna foto_url OK (ou já existia).")


if __name__ == "__main__":
    main()
