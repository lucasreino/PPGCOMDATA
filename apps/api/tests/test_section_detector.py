from app.services.section_detector import detect_sections, split_text_by_sections


def test_detect_sections_finds_lattes_headers(sample_lattes_text):
    boundaries = detect_sections(sample_lattes_text)
    names = [b["nome_secao"] for b in boundaries]
    assert "Projetos de pesquisa" in names
    assert "Produção bibliográfica" in names
    assert "Participação em eventos" in names


def test_detect_orientacoes_subsections():
    text = """
Dados gerais
Nome: Prof. Exemplo
Orientações e supervisões concluídas
Mestrado - Aluno A - 2022
Orientações e supervisões em andamento
Doutorado - Aluno B - 2024
Bancas
"""
    names = [b["nome_secao"] for b in detect_sections(text)]
    assert "Orientações e supervisões concluídas" in names
    assert "Orientações e supervisões em andamento" in names


def test_split_text_by_sections_returns_chunks(sample_lattes_text):
    boundaries = detect_sections(sample_lattes_text)
    chunks = split_text_by_sections(sample_lattes_text, boundaries)
    assert len(chunks) >= 3
    projeto = next(c for c in chunks if c["nome_secao"] == "Projetos de pesquisa")
    assert "FAPEMA" in projeto["texto_secao"]
