"""Testes da lógica de reconciliação XML × PDF."""

from types import SimpleNamespace

from app.models.enums import FonteDado, StatusValidacao
from app.services.xml_pdf_reconciler import (
    _match_orientacao,
    _match_producao,
    _match_projeto,
    _reconcile_lists,
    _texts_similar,
)


def test_texts_similar_exact_and_substring():
    assert _texts_similar("Artigo sobre Mídia", "artigo sobre midia")
    assert _texts_similar(
        "A sociedade em rede no ciberespaço",
        "Estudo: A sociedade em rede no ciberespaço e podcasts",
    )
    assert not _texts_similar("A", "B")


def test_match_producao_requires_tipo_and_year():
    pdf = SimpleNamespace(tipo="artigo", titulo="Título X", ano=2024)
    xml = SimpleNamespace(tipo="artigo", titulo="Titulo X", ano=2024)
    assert _match_producao(pdf, xml)
    xml2 = SimpleNamespace(tipo="livro", titulo="Titulo X", ano=2024)
    assert not _match_producao(pdf, xml2)


def test_match_orientacao_by_name_or_title():
    pdf = SimpleNamespace(
        nome_orientando="Maria Silva",
        titulo_trabalho="",
        ano_conclusao=2020,
        ano_inicio=None,
    )
    xml = SimpleNamespace(
        nome_orientando="Maria Silva",
        titulo_trabalho="Estudo de caso",
        ano_conclusao=2020,
        ano_inicio=None,
    )
    assert _match_orientacao(pdf, xml)


def test_reconcile_lists_xml_wins_over_pdf():
    upload = SimpleNamespace(id="up-1", professor_id="prof-1")
    pdf = SimpleNamespace(
        id="pdf-1",
        fonte_dado=FonteDado.PDF_LATTES,
        status_validacao=StatusValidacao.PENDENTE,
        titulo="Projeto Alpha",
        ano_inicio=2023,
        observacoes=None,
    )
    xml = SimpleNamespace(
        id="xml-1",
        fonte_dado=FonteDado.XML_LATTES,
        status_validacao=StatusValidacao.PENDENTE,
        titulo="Projeto Alpha",
        ano_inicio=2023,
        observacoes=None,
    )

    class FakeSession:
        def add(self, _):
            pass

        def exec(self, _):
            class R:
                def first(self):
                    return None

                def all(self):
                    return []

            return R()

    stats = _reconcile_lists(
        FakeSession(),
        upload,
        "projetos",
        [pdf],
        [xml],
        _match_projeto,
        lambda r: r.titulo,
    )
    assert stats.pares_encontrados == 1
    assert stats.xml_confirmados == 1
    assert stats.pdf_descartados == 1
    assert pdf.status_validacao == StatusValidacao.DESCARTADO
    assert xml.status_validacao == StatusValidacao.CONFIRMADO
