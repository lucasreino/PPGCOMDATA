from app.services.extraction_registry import resolve_extraction_profile


def test_resolve_orientacoes():
    assert resolve_extraction_profile("Orientações e supervisões") == "orientacoes"
    assert (
        resolve_extraction_profile("Orientações e supervisões concluídas")
        == "orientacoes"
    )


def test_resolve_bancas():
    assert resolve_extraction_profile("Bancas") == "bancas"


def test_resolve_formacao():
    assert resolve_extraction_profile("Formação acadêmica/titulação") == "formacao"


def test_resolve_perfil():
    assert resolve_extraction_profile("Dados gerais") == "perfil"


def test_resolve_padrao():
    assert resolve_extraction_profile("Projetos de pesquisa") == "padrao"
