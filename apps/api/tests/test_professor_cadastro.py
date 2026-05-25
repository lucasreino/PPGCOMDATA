"""Testes do cadastro de docente."""

from app.services.professor_cadastro import (
    build_observacoes,
    parse_lattes_id,
)


def test_parse_lattes_id_from_link():
    assert parse_lattes_id("http://lattes.cnpq.br/9088752631596667", None) == "9088752631596667"


def test_parse_lattes_id_explicit():
    assert parse_lattes_id(None, "1234567890123456") == "1234567890123456"


def test_build_observacoes():
    obs = build_observacoes("Grupo X", "Tema A; Tema B")
    assert "Grupo de pesquisa: Grupo X" in obs
    assert "Temáticas: Tema A; Tema B" in obs
