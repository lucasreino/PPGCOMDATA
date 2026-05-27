import json
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from app.models.core import Professor
from app.models.data import Producao
from app.services.journal_hindex_catalog import (
    JournalHindexHit,
    apply_journal_hindex_to_producoes,
    load_journal_hindex_catalog,
    load_journal_hindex_from_csv,
    lookup_journal_hindex,
)


def test_lookup_journal_hindex_by_issn(tmp_path: Path):
    data = {
        "journals": [
            {"titulo": "InTexto", "issn": "18078583", "h_index": 20.0},
        ],
    }
    p = tmp_path / "m.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    by_issn, by_titulo = load_journal_hindex_catalog(p)
    hit, method = lookup_journal_hindex("1807-8583", None, by_issn, by_titulo, None, None)
    assert method == "issn"
    assert hit == JournalHindexHit(h_index=20.0)


def test_load_journal_hindex_from_csv(tmp_path: Path):
    csv_path = tmp_path / "revistas.csv"
    csv_path.write_text(
        "nome,issn,h_index\n"
        "InTexto,18078583,20.0\n"
        "Sem h-index,12345678,\n"
        "Decimal,99999999,8.5\n",
        encoding="utf-8",
    )
    data = load_journal_hindex_from_csv(csv_path)
    assert len(data["journals"]) == 2
    assert data["journals"][0]["h_index"] == 20.0
    assert data["journals"][1]["h_index"] == 8.5


def test_apply_journal_hindex_to_producoes(tmp_path: Path):
    data = {
        "journals": [
            {"titulo": "Communication Research", "issn": "00936502", "h_index": 76.0},
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

        stats = apply_journal_hindex_to_producoes(session, json_path=p)
        assert stats["atualizado"] == 1
        prod = session.exec(select(Producao)).first()
        assert prod is not None
        assert prod.journal_h_index == 76.0

        stats2 = apply_journal_hindex_to_producoes(session, json_path=p)
        assert stats2["ja_ok"] == 1
        assert stats2["atualizado"] == 0
