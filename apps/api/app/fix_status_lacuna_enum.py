"""Converte status_tratamento de enum PG (ABERTA) para varchar (aberta)."""

from sqlalchemy import text

from app.database import engine


def main() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE alertas_lacunas
                ALTER COLUMN status_tratamento TYPE varchar(32)
                USING (
                    CASE lower(status_tratamento::text)
                        WHEN 'aberta' THEN 'aberta'
                        WHEN 'em_analise' THEN 'em_analise'
                        WHEN 'resolvida' THEN 'resolvida'
                        ELSE lower(status_tratamento::text)
                    END
                )
                """
            )
        )
        conn.execute(text("DROP TYPE IF EXISTS statustratamentolacuna"))
    print("status_tratamento migrado para varchar(32)")


if __name__ == "__main__":
    main()
