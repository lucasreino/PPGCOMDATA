import json
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from app.models.core import Professor
from app.models.data import Producao
from app.services.scholar_metrics_catalog import (
    ScholarMetricsHit,
    apply_scholar_metrics_to_producoes,
    load_scholar_metrics_catalog,
    lookup_scholar_metrics,
)


def test_lookup_scholar_metrics_by_issn(tmp_path: Path):
    data = {
        "metrics_year": 2024,
        "journals": [
            {
                "titulo": "Journal of Communication",
                "issn": "00219915",
                "h5_index": 89,
                "h5_median": 124,
            }
        ],
    }
    p = tmp_path / "m.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    by_issn, by_titulo, year = load_scholar_metrics_catalog(p)
    assert year == 2024
    hit, method = lookup_scholar_metrics("0021-9915", None, by_issn, by_titulo, None, None)
    assert method == "issn"
    assert hit == ScholarMetricsHit(h5_index=89, h5_median=124, metrics_year=2024)


def test_apply_scholar_metrics_to_producoes(tmp_path: Path):
    data = {
        "metrics_year": 2024,
        "journals": [
            {"titulo": "Communication Research", "issn": "00936502", "h5_index": 76},
        ],
    }
    p = tmp_path / "m.json"
    p.write_text(json.dumps(data), encoding="utf-8")

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        prof = Professor(nome_completo="Test", status=True)
        session.add(prof)
        session.commit()
        session.refresh(prof)
        session.add(
            Producao(
                professor_id=str(prof.id),
                tipo="artigo",
                titulo="Paper",
                veiculo="Communication Research",
                ano=2023,
                issn="0093-6502",
            )
        )
        session.commit()

        stats = apply_scholar_metrics_to_producoes(session, json_path=p)
        assert stats["atualizado"] == 1
        prod = session.exec(select(Producao)).first()
        assert prod is not None
        assert prod.scholar_h5_index == 76
        assert prod.scholar_metrics_year == 2024

        stats2 = apply_scholar_metrics_to_producoes(session, json_path=p)
        assert stats2["ja_ok"] == 1
        assert stats2["atualizado"] == 0
