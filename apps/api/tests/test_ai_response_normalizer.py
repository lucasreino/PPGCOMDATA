from app.schemas.ai import AIProducaoSchema, AIProjetoSchema, LattesExtractionResultSchema
from app.services.ai_extractor import _validate_extraction_raw
from app.services.ai_response_normalizer import (
    coerce_autores,
    coerce_optional_year,
    normalize_item_fields,
    normalize_producao_tipo,
)


def test_coerce_optional_year_atual_returns_none():
    assert coerce_optional_year("Atual") is None
    assert coerce_optional_year("em andamento") is None
    assert coerce_optional_year(2023) == 2023
    assert coerce_optional_year("publicado em 2021") == 2021


def test_coerce_autores_list_to_string():
    assert coerce_autores(["Silva, J.", "Santos, M."]) == "Silva, J.; Santos, M."


def test_normalize_producao_tipo_from_section():
    assert (
        normalize_producao_tipo("Artigo Completo", section_name="Artigos completos publicados em periódicos")
        == "artigo"
    )
    assert (
        normalize_producao_tipo(None, section_name="Livros publicados/organizados")
        == "livro"
    )


def test_normalize_item_fields_producao_bibliografica():
    raw = {
        "tipo": "Artigo em periódico",
        "titulo": "Comunicação e política",
        "ano": "Atual",
        "autores": ["João Silva", "Maria Santos"],
        "veiculo": "Revista Brasileira",
        "confianca_ia": "Média",
        "trecho_original": "Comunicação e política. Revista Brasileira, 2024.",
    }
    item = normalize_item_fields(
        raw,
        section_name="Artigos completos publicados em periódicos",
    )
    validated = AIProducaoSchema(**item)
    assert validated.tipo == "artigo"
    assert validated.ano is None
    assert validated.autores == "João Silva; Maria Santos"
    assert validated.confianca_ia.value == "media"


def test_normalize_item_fields_projeto_ano_fim_atual():
    raw = {
        "titulo": "Projeto X",
        "tipo": "pesquisa científica",
        "situacao": "em andamento",
        "ano_inicio": 2020,
        "ano_fim": "Atual",
        "confianca_ia": "alta",
        "trecho_original": "Projeto X",
    }
    item = normalize_item_fields(raw)
    validated = AIProjetoSchema(**item)
    assert validated.ano_fim is None
    assert validated.tipo.value == "pesquisa"


def test_validate_extraction_raw_recovers_partial_producoes():
    raw = {
        "projetos": [],
        "eventos": [],
        "financiamentos": [],
        "lacunas": [],
        "producoes": [
            {
                "tipo": "artigo",
                "titulo": "Válido",
                "ano": 2022,
                "veiculo": "Revista X",
                "confianca_ia": "media",
                "trecho_original": "Válido",
            },
            {
                "tipo": "artigo",
                "ano": "inválido",
                "confianca_ia": "xyz",
            },  # sem título/trecho → descartado na recuperação
            {
                "tipo": "capítulo de livro",
                "titulo": "Capítulo OK",
                "ano": "2020-2021",
                "autores": ["Autor A"],
                "veiculo": "Editora Y",
                "confianca_ia": "Alta",
                "trecho_original": "Capítulo OK",
            },
        ],
    }
    result = _validate_extraction_raw(
        raw,
        "padrao",
        section_name="Artigos completos publicados em periódicos",
    )
    assert isinstance(result, LattesExtractionResultSchema)
    assert len(result.producoes) == 2
    assert result.producoes[0].titulo == "Válido"
    assert result.producoes[1].titulo == "Capítulo OK"
    assert result.producoes[1].tipo == "capitulo"
    assert result.producoes[1].ano == 2020
