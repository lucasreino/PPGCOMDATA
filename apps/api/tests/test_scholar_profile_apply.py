from sqlmodel import Session, SQLModel, create_engine

from app.models.core import Professor
from app.models.data import Producao
from app.services.scholar_profile_apply import (
    match_scholar_publication,
    resolve_professor_for_profile,
)
from app.services.scholar_profile_parser import (
    ScholarProfileData,
    ScholarProfileMetrics,
    ScholarProfilePublication,
)


def _prod(titulo: str, ano: int | None = None) -> Producao:
    return Producao(
        professor_id="p1",
        tipo="artigo",
        titulo=titulo,
        ano=ano,
    )


def test_match_titulo_exato():
    pub = ScholarProfilePublication(
        title="SEO no jornalismo: títulos testáveis e suas implicações",
        year=2019,
        citations=16,
    )
    prod = _prod(
        "SEO no jornalismo: títulos testáveis e suas implicações",
        2019,
    )
    matched, mode = match_scholar_publication(pub, [prod])
    assert matched is prod
    assert mode == "titulo_exato"


def test_match_titulo_similar_com_ano():
    pub = ScholarProfilePublication(
        title="Ciberjornalismo em dispositivos móveis: uma análise da conjuntura brasileira",
        year=2012,
        citations=8,
    )
    prod = _prod(
        "Ciberjornalismo em dispositivos moveis: uma analise da conjuntura brasileira",
        2012,
    )
    matched, mode = match_scholar_publication(pub, [prod])
    assert matched is prod
    assert mode.startswith("titulo_")


def test_match_ambiguo_mesmo_titulo():
    pub = ScholarProfilePublication(title="Artigo X", year=2020, citations=3)
    a = _prod("Artigo X", 2019)
    b = _prod("Artigo X", 2021)
    matched, mode = match_scholar_publication(pub, [a, b])
    assert matched is None
    assert mode == "ambiguo"


def test_resolve_professor_por_nome_exato():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    profile = ScholarProfileData(
        scholar_user_id="TESTUSER1",
        profile_url=None,
        name="Lucas Santiago Arraes Reino",
        affiliation="UFMA",
        metrics=ScholarProfileMetrics(1, None, 1, None, 0, None),
        publications=[],
    )
    with Session(engine) as session:
        session.add(
            Professor(
                nome_completo="Lucas Santiago Arraes Reino",
                email="lucas@ufma.br",
            )
        )
        session.commit()
        prof, mode = resolve_professor_for_profile(session, profile)
        assert prof is not None
        assert mode == "nome_exato"


def test_resolve_professor_nome_tokens_lattes_curto():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    profile = ScholarProfileData(
        scholar_user_id="Q61X3XUAAAAJ",
        profile_url=None,
        name="Lucas Santiago Arraes Reino",
        affiliation="UFMA",
        metrics=ScholarProfileMetrics(197, 87, 7, 5, 3, 2, since_year=2021),
        publications=[],
    )
    with Session(engine) as session:
        session.add(Professor(nome_completo="Lucas Reino", id_lattes="5487269670962081"))
        session.commit()
        prof, mode = resolve_professor_for_profile(session, profile)
        assert prof is not None
        assert mode == "nome_tokens"


def test_resolve_professor_nome_ambiguo():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    profile = ScholarProfileData(
        scholar_user_id="X",
        profile_url=None,
        name="Maria Silva Santos",
        affiliation=None,
        metrics=ScholarProfileMetrics(0, None, 0, None, 0, None),
        publications=[],
    )
    with Session(engine) as session:
        session.add(Professor(nome_completo="Maria Silva Santosa"))
        session.add(Professor(nome_completo="Maria Silva Santoz"))
        session.commit()
        prof, mode = resolve_professor_for_profile(session, profile, min_name_ratio=0.85)
        assert prof is None
        assert mode == "nome_ambiguo"
