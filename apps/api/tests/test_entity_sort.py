from datetime import date, datetime

from app.models.enums import StatusOrientacao
from app.services.entity_sort import sort_entities_newest_first


class _Row:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_projetos_newest_first_by_end_year():
    rows = [
        _Row(ano_inicio=2010, ano_fim=2015, created_at=datetime(2020, 1, 1)),
        _Row(ano_inicio=2022, ano_fim=None, created_at=datetime(2020, 1, 1)),
        _Row(ano_inicio=2018, ano_fim=2020, created_at=datetime(2020, 1, 1)),
    ]
    sorted_rows = sort_entities_newest_first(rows, "projetos")
    assert sorted_rows[0].ano_inicio == 2022
    assert sorted_rows[1].ano_fim == 2020
    assert sorted_rows[2].ano_fim == 2015


def test_orientacoes_by_conclusao():
    rows = [
        _Row(ano_inicio=2015, ano_conclusao=2018, created_at=datetime(2020, 1, 1)),
        _Row(ano_inicio=2020, ano_conclusao=2024, created_at=datetime(2020, 1, 1)),
        _Row(ano_inicio=2019, ano_conclusao=None, status=StatusOrientacao.EM_ANDAMENTO, created_at=datetime(2020, 1, 1)),
    ]
    sorted_rows = sort_entities_newest_first(rows, "orientacoes")
    assert sorted_rows[0].ano_conclusao == 2024
    assert sorted_rows[1].status == StatusOrientacao.EM_ANDAMENTO


def test_producoes_by_ano():
    rows = [
        _Row(ano=2019, created_at=datetime(2020, 1, 1)),
        _Row(ano=2023, created_at=datetime(2020, 1, 1)),
        _Row(ano=2021, created_at=datetime(2020, 1, 1)),
    ]
    assert [r.ano for r in sort_entities_newest_first(rows, "producoes")] == [2023, 2021, 2019]


def test_lacunas_by_prazo():
    rows = [
        _Row(prazo=date(2024, 6, 1), created_at=datetime(2020, 1, 1)),
        _Row(prazo=date(2026, 1, 1), created_at=datetime(2020, 1, 1)),
        _Row(prazo=None, created_at=datetime(2025, 1, 1)),
    ]
    sorted_rows = sort_entities_newest_first(rows, "lacunas")
    assert sorted_rows[0].prazo == date(2026, 1, 1)
