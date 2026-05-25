from app.services.producao_coautoria import artigo_work_key, group_artigos_by_work


def test_artigo_work_key_same_title_different_doi():
    k1 = artigo_work_key("Título X", 2024, None)
    k2 = artigo_work_key("Título X", 2024, None)
    assert k1 == k2
    k3 = artigo_work_key("Título X", 2023, None)
    assert k1 != k3


def test_group_artigos_by_work():
    class Row:
        def __init__(self, titulo, ano, tipo="artigo", doi=None):
            self.titulo = titulo
            self.ano = ano
            self.tipo = tipo
            self.doi = doi

    rows = [
        Row("A", 2024),
        Row("A", 2024),
        Row("B", 2024),
    ]
    groups = group_artigos_by_work(rows)
    assert len(groups) == 2
    assert len(groups[list(groups.keys())[0]]) == 2
