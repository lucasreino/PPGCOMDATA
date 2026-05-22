from sqlmodel import Session, SQLModel, create_engine

from app.models.core import Professor
from app.models.data import Orientacao
from app.models.enums import StatusOrientacao, TipoOrientacao
from app.services.orientacoes_analytics import build_orientacoes_insights


def test_orientacoes_insights_grouping():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        prof = Professor(nome_completo="Maria", status=True)
        session.add(prof)
        session.commit()
        session.refresh(prof)
        pid = str(prof.id)

        session.add(
            Orientacao(
                professor_id=pid,
                tipo=TipoOrientacao.MESTRADO,
                status=StatusOrientacao.CONCLUIDA,
                nome_orientando="Ana",
                ano_conclusao=2024,
            )
        )
        session.add(
            Orientacao(
                professor_id=pid,
                tipo=TipoOrientacao.DOUTORADO,
                status=StatusOrientacao.EM_ANDAMENTO,
                nome_orientando="Bruno",
                ano_inicio=2023,
            )
        )
        session.commit()

        def apply_prof(stmt, model):
            return stmt

        def apply_val(stmt, model):
            return stmt

        result = build_orientacoes_insights(session, apply_prof, apply_val, None, None)
        assert result["total"] == 2
        assert result["concluidas"] == 1
        assert result["em_andamento"] == 1
        assert len(result["por_tipo_grupos"]) == 2
        assert len(result["por_status_grupos"]) == 2
        assert result["por_professor_grupos"][0]["count"] == 2
