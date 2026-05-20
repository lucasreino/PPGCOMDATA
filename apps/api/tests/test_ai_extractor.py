from app.services.ai_extractor import generate_mock_extraction


def test_mock_extraction_projects_section():
    result = generate_mock_extraction(
        "Projetos de pesquisa",
        "Projeto financiado pela FAPEMA em 2024.",
    )
    assert len(result["projetos"]) >= 1
    assert len(result["financiamentos"]) >= 1
    assert result["projetos"][0]["financiamento_mencionado"] is True


def test_mock_extraction_events_section():
    result = generate_mock_extraction(
        "Participação em eventos",
        "Apresentou trabalho na Compós 2025.",
    )
    assert len(result["eventos"]) >= 1


def test_mock_extraction_productions_section():
    result = generate_mock_extraction(
        "Produção bibliográfica",
        "Artigo publicado em periódico indexado.",
    )
    assert len(result["producoes"]) >= 1
