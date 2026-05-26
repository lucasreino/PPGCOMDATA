from app.services.grupo_pesquisa_lattes import (
    extract_codigo_dgp,
    is_lattes_projeto_grupo_pesquisa,
)


def test_is_grupo_by_title():
    assert is_lattes_projeto_grupo_pesquisa(
        "Grupo de Pesquisa em Comunicação e Sociedade (COPS)"
    )
    assert is_lattes_projeto_grupo_pesquisa("Grupo de Estudos de CiberJornalismo")
    assert not is_lattes_projeto_grupo_pesquisa(
        "A comunicação no Sul do Maranhão: mapeamento das mídias"
    )


def test_is_grupo_by_natureza_outro():
    assert is_lattes_projeto_grupo_pesquisa("Projeto institucional X", natureza="OUTRO")


def test_extract_codigo_dgp():
    assert extract_codigo_dgp(
        "Grupo X",
        "Espelho em http://dgp.cnpq.br/dgp/espelhogrupo/0030069073641405",
    ) == "0030069073641405"
