"""Índices compostos para consultas frequentes. Execute: python -m app.migrate_perf_indexes"""

from __future__ import annotations

import os
import sys

from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_producao_prof_status ON producoes (professor_id, status_validacao)",
    "CREATE INDEX IF NOT EXISTS idx_projeto_prof_status ON projetos (professor_id, status_validacao)",
    "CREATE INDEX IF NOT EXISTS idx_evento_prof_status ON eventos (professor_id, status_validacao)",
    "CREATE INDEX IF NOT EXISTS idx_financiamento_prof_status ON financiamentos (professor_id, status_validacao)",
    "CREATE INDEX IF NOT EXISTS idx_orientacao_prof_status ON orientacoes (professor_id, status_validacao)",
    "CREATE INDEX IF NOT EXISTS idx_upload_prof_data ON curriculo_uploads (professor_id, data_upload DESC)",
    "CREATE INDEX IF NOT EXISTS idx_lacuna_prof_resolvido ON alertas_lacunas (professor_id, resolvido)",
]


def main() -> None:
    with engine.begin() as conn:
        for stmt in INDEXES:
            conn.execute(text(stmt))
            print(f"OK: {stmt[:60]}...")
    print("Índices de performance aplicados.")


if __name__ == "__main__":
    main()
