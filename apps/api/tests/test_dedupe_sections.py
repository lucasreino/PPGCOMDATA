from app.services.extraction_registry import (
    is_bibliographic_parent_section,
    should_extract_producoes,
    resolve_extraction_profile,
)


def test_parent_section_skips_producoes():
    assert is_bibliographic_parent_section("Produção bibliográfica")
    assert not should_extract_producoes("Produção bibliográfica")


def test_leaf_section_extracts_producoes():
    name = "Artigos completos publicados em periódicos"
    assert not is_bibliographic_parent_section(name)
    assert should_extract_producoes(name)


def test_eventos_organizacao_profile():
    assert resolve_extraction_profile("Organização de eventos") == "eventos_organizacao"


def test_mock_would_not_double_parent_and_child():
    parent = "Produção bibliográfica"
    child = "Artigos completos publicados em periódicos"
    assert not should_extract_producoes(parent)
    assert should_extract_producoes(child)
