"""Testes do serviço de indicadores consolidados."""

from app.services.indicator_service import IndicatorFilters, _norm_tipo_producao


def test_norm_tipo_producao():
    assert _norm_tipo_producao("artigo") == "artigos"
    assert _norm_tipo_producao("capítulo") == "capitulos"
    assert _norm_tipo_producao("xyz") == "outras"


def test_indicator_filters_query_params():
    f = IndicatorFilters(professor_id="abc", ano_inicio=2020, apenas_validados=True)
    q = f.query_params()
    assert q["professor_id"] == "abc"
    assert q["ano_inicio"] == 2020
    assert q["apenas_validados"] is True
