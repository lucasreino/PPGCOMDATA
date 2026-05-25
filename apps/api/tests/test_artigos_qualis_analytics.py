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
        assert result["total_registros"] == 2
        assert result["por_estrato"]["A1"]["count"] == 1
        assert result["por_estrato"]["A2"]["count"] == 1
        assert result["por_revista"][0]["veiculo"] in ("Revista X", "Revista Y")
        assert "Alice" in result["professor_por_estrato"]
        assert result["professor_por_estrato"]["Alice"]["A1"] == 1


def test_artigos_qualis_dedup_coautoria():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        p1 = Professor(nome_completo="Alice", status=True)
        p2 = Professor(nome_completo="Bob", status=True)
        p3 = Professor(nome_completo="Carlos", status=True)
        session.add_all([p1, p2, p3])
        session.commit()
        for p in (p1, p2, p3):
            session.refresh(p)

        titulo = "Desinformação eleitoral no Brasil: 2022 e 2024"
        for prof in (p1, p2, p3):
            session.add(
                Producao(
                    professor_id=str(prof.id),
                    tipo="artigo",
                    titulo=titulo,
                    veiculo="Revista Comunicação",
                    ano=2024,
                    qualis="A1",
                    autores="Alice; Bob; Carlos",
                )
            )
        session.commit()

        def apply_prof(stmt, model):
            return stmt

        def apply_val(stmt, model):
            return stmt

        result = build_artigos_qualis_insights(session, apply_prof, apply_val, None, None)
        assert result["total_artigos"] == 1
        assert result["total_registros"] == 3
        assert result["por_estrato"]["A1"]["count"] == 1
        assert result["professor_por_estrato"]["Alice"]["A1"] == 1
        assert result["professor_por_estrato"]["Bob"]["A1"] == 1
        assert result["professor_por_estrato"]["Carlos"]["A1"] == 1
        assert len(result["publicacoes_por_docente"]) == 3
        artigo = result["artigos"][0]
        assert artigo["eh_coautoria"] is True
        assert artigo["num_docentes_ppgcom"] == 3
        assert set(artigo["docentes_ppgcom"]) == {"Alice", "Bob", "Carlos"}
