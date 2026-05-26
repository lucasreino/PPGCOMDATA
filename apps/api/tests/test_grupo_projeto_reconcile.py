from sqlmodel import Session, SQLModel, create_engine, select

from app.models.core import Professor
from app.models.data import GrupoPesquisaDocente, Projeto
from app.models.enums import FonteDado, StatusValidacao, TipoProjeto
from app.services.grupo_projeto_reconcile import reconcile_projetos_misclassified_as_grupos


def test_reconcile_descarta_projeto_e_cria_grupo():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        prof = Professor(nome_completo="Teste", status=True)
        session.add(prof)
        session.commit()
        session.refresh(prof)

        pid = str(prof.id)
        for titulo in (
            "Grupo de Pesquisa Teste (GPX)",
            "Projeto real de pesquisa comunitária",
        ):
            session.add(
                Projeto(
                    professor_id=pid,
                    titulo=titulo,
                    tipo=TipoProjeto.PESQUISA,
                    fonte_dado=FonteDado.XML_LATTES,
                    status_validacao=StatusValidacao.PENDENTE,
                )
            )
            session.commit()

        metrics = reconcile_projetos_misclassified_as_grupos(session)
        assert metrics["candidatos_grupo"] == 1
        assert metrics["projetos_descartados"] == 1
        assert metrics["grupos_criados"] == 1

        projetos = list(session.exec(select(Projeto)).all())
        grupos = list(session.exec(select(GrupoPesquisaDocente)).all())
        assert len(grupos) == 1
        assert grupos[0].nome_grupo.startswith("Grupo de Pesquisa")

        descartados = [p for p in projetos if p.status_validacao == StatusValidacao.DESCARTADO]
        ativos = [p for p in projetos if p.status_validacao != StatusValidacao.DESCARTADO]
        assert len(descartados) == 1
        assert len(ativos) == 1
        assert ativos[0].titulo.startswith("Projeto real")
