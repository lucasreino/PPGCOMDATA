import pytest
from app.services.pdf_processor import extract_text_by_page, detect_pdf_quality, extract_full_text
from app.services.section_detector import detect_sections, split_text_by_sections
from app.services.ai_extractor import generate_mock_extraction


@pytest.fixture
def sample_lattes_text() -> str:
    return """
Dados gerais
Nome: Prof. Dr. Exemplo

Projetos de pesquisa
Projeto de pesquisa em andamento (2024 - Atual) intitulado Comunicação Digital,
financiado pela FAPEMA sob processo U-12345/23.

Produção bibliográfica
Artigos completos publicados em periódicos
Artigo publicado na Revista Brasileira de Ciências da Comunicação, v. 47, 2024.

Participação em eventos
Apresentação do trabalho Comunicação e Algoritmos no Encontro da Compós 2025.
"""
