from sqlmodel import Session, SQLModel, create_engine

from app.models.core import Professor
from app.models.data import Producao
from app.services.artigos_qualis_analytics import build_artigos_qualis_insights


def test_artigos_qualis_grouping():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        p1 = Professor(nome_completo="Alice", status=True)
        p2 = Professor(nome_completo="Bob", status=True)
        session.add(p1)
        session.add(p2)
        session.commit()
        session.refresh(p1)
        session.refresh(p2)

        session.add(
            Producao(
                professor_id=str(p1.id),
                tipo="artigo",
                titulo="Art 1",
                veiculo="Revista X",
                ano=2024,
                qualis="A1",
            )
        )
        session.add(
            Producao(
                professor_id=str(p2.id),
                tipo="artigo",
                titulo="Art 2",
                veiculo="Revista Y",
                ano=2023,
                qualis="A2",
            )
        )
        session.add(
            Producao(
                professor_id=str(p1.id),
                tipo="livro",
                titulo="Livro",
                ano=2022,
            )
        )
        session.commit()

        def apply_prof(stmt, model):
            return stmt

        def apply_val(stmt, model):
            return stmt

        result = build_artigos_qualis_insights(session, apply_prof, apply_val, None, None)
        assert result["total_artigos"] == 2
        assert result["por_estrato"]["A1"]["count"] == 1
        assert result["por_estrato"]["A2"]["count"] == 1
        assert result["por_revista"][0]["veiculo"] in ("Revista X", "Revista Y")
        assert "Alice" in result["professor_por_estrato"]
        assert result["professor_por_estrato"]["Alice"]["A1"] == 1
