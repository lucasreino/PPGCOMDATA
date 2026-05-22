"""Testes leves das agregações SQL de estatísticas."""

from sqlmodel import Session, SQLModel, create_engine, select

from app.models.core import Professor
from app.models.data import Producao
from app.models.enums import StatusValidacao
from app.services.analytics_sql import build_analytics_stats_sql
from app.services.indicator_service import IndicatorFilters, IndicatorService


def _noop_validacao(stmt, _model):
    return stmt


def test_build_analytics_stats_empty_db():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        def apply_prof(stmt, model):
            return stmt

        result = build_analytics_stats_sql(session, apply_prof, _noop_validacao, None, None)
        assert result["total_producoes"] == 0
        assert result["lacunas"]["total"] == 0


def test_build_analytics_stats_counts_producao():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        prof = Professor(nome_completo="Teste Silva", status=True)
        session.add(prof)
        session.commit()
        session.refresh(prof)
        session.add(
            Producao(
                professor_id=str(prof.id),
                tipo="artigo",
                titulo="Artigo 1",
                ano=2024,
                qualis="A1",
            )
        )
        session.add(
            Producao(
                professor_id=str(prof.id),
                tipo="livro",
                titulo="Livro 1",
                ano=2023,
            )
        )
        session.commit()

        pid = str(prof.id)

        def apply_prof(stmt, model):
            return stmt.where(model.professor_id == pid)

        result = build_analytics_stats_sql(session, apply_prof, _noop_validacao, None, None)
        assert result["total_producoes"] == 2
        assert result["producoes_por_tipo"]["artigo"] == 1
        assert result["producoes_por_qualis"]["A1"] == 1


def test_indicator_service_delegates_to_sql():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        stats = IndicatorService(session, IndicatorFilters()).get_analytics_stats()
        assert "total_producoes" in stats
        assert "validacao_pendentes" in stats
