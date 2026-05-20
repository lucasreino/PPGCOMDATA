from app.services.ai_extractor import generate_mock_extraction


def test_mock_extraction_projects_section():
    result = generate_mock_extraction(
        "Projetos de pesquisa",
        "Projeto financiado pela FAPEMA em 2024.",
        "padrao",
    )
    assert len(result["projetos"]) >= 1


def test_mock_extraction_events_section():
    result = generate_mock_extraction(
        "Participação em eventos",
        "Apresentou trabalho na Compós 2025.",
        "padrao",
    )
    assert len(result["eventos"]) >= 1


def test_mock_extraction_orientacoes_section():
    result = generate_mock_extraction(
        "Orientações e supervisões",
        "Orientou dissertação de mestrado.",
        "orientacoes",
    )
    assert len(result["orientacoes"]) >= 1


def test_mock_extraction_formacao_section():
    result = generate_mock_extraction(
        "Formação acadêmica/titulação",
        "Doutorado em Comunicação.",
        "formacao",
    )
    assert len(result["formacoes"]) >= 1
