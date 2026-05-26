from app.services.grupos_pesquisa_sync import parse_grupos_from_observacoes


def test_parse_grupo_simples():
    obs = "Grupo de pesquisa: Gciber\nTemáticas: Ciberjornalismo"
    assert parse_grupos_from_observacoes(obs) == [
        ("Gciber", "Ciberjornalismo"),
    ]


def test_parse_grupo_multiplo_com_barra():
    obs = (
        "Grupo de pesquisa: Grupo A / Grupo B\n"
        "Temáticas: Linha temática X"
    )
    assert parse_grupos_from_observacoes(obs) == [
        ("Grupo A", "Linha temática X"),
        ("Grupo B", "Linha temática X"),
    ]
