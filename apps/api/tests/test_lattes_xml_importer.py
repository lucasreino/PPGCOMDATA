"""Testes do importador XML Lattes."""

from pathlib import Path

import pytest

from app.services.lattes_xml_importer import (
    _load_xml_root,
    _parse_lattes_date,
    resolve_xml_path_for_lattes_id,
)


EXTENDED_MINI_XML = """<?xml version="1.0" encoding="ISO-8859-1"?>
<CURRICULO-VITAE NUMERO-IDENTIFICADOR="1234567890123456" DATA-ATUALIZACAO="15052026">
  <DADOS-GERAIS NOME-COMPLETO="Prof Teste"/>
  <PRODUCAO-BIBLIOGRAFICA>
    <LIVROS-PUBLICADOS-OU-ORGANIZADOS>
      <LIVRO-PUBLICADO-OU-ORGANIZADO>
        <DADOS-BASICOS-DO-LIVRO TITULO-DO-LIVRO="Livro Teste" ANO="2020"/>
      </LIVRO-PUBLICADO-OU-ORGANIZADO>
    </LIVROS-PUBLICADOS-OU-ORGANIZADOS>
    <CAPITULOS-DE-LIVROS-PUBLICADOS>
      <CAPITULO-DE-LIVRO-PUBLICADO>
        <DADOS-BASICOS-DO-CAPITULO TITULO-DO-CAPITULO-DO-LIVRO="Cap Teste" ANO="2021"/>
      </CAPITULO-DE-LIVRO-PUBLICADO>
    </CAPITULOS-DE-LIVROS-PUBLICADOS>
  </PRODUCAO-BIBLIOGRAFICA>
  <ORIENTACOES-CONCLUIDAS>
    <ORIENTACAO TIPO="mestrado" STATUS="concluida" NOME-ORIENTANDO="Aluno X"
      TITULO-DO-TRABALHO="Tese Y" ANO-CONCLUSAO="2019"/>
  </ORIENTACOES-CONCLUIDAS>
  <PARTICIPACAO-EM-BANCA-TRABALHOS-CONCLUSAO>
    <PARTICIPACAO-EM-BANCA TIPO="defesa" NIVEL="mestrado" NOME-CANDIDATO="Cand Z"
      TITULO-DO-TRABALHO="Defesa W" ANO="2018"/>
  </PARTICIPACAO-EM-BANCA-TRABALHOS-CONCLUSAO>
  <PARTICIPACAO-EM-EVENTOS-CONGRESSOS>
    <PARTICIPACAO-EM-EVENTO NOME-DO-EVENTO="Congresso A" ANO="2022"
      TIPO-PARTICIPACAO="apresentacao" EH-ORGANIZACAO="NAO"/>
  </PARTICIPACAO-EM-EVENTOS-CONGRESSOS>
</CURRICULO-VITAE>
"""

MINI_XML = """<?xml version="1.0" encoding="ISO-8859-1"?>
<CURRICULO-VITAE NUMERO-IDENTIFICADOR="1234567890123456" DATA-ATUALIZACAO="15052026">
  <DADOS-GERAIS NOME-COMPLETO="Prof Teste" NOME-EM-CITACOES-BIBLIOGRAFICAS="TESTE, P."
    ORCID-ID="https://orcid.org/0000-0000-0000-0001">
    <RESUMO-CV TEXTO-RESUMO-CV-RH="Resumo de teste."/>
  </DADOS-GERAIS>
  <FORMACAO-ACADEMICA-TITULACAO>
    <DOUTORADO NIVEL="4" NOME-INSTITUICAO="UFF" NOME-CURSO="Comunicacao"
      ANO-DE-INICIO="2018" ANO-DE-CONCLUSAO="2022" FLAG-BOLSA="SIM"
      NOME-AGENCIA="CAPES, Brasil."/>
  </FORMACAO-ACADEMICA-TITULACAO>
  <PRODUCAO-BIBLIOGRAFICA>
    <ARTIGOS-PUBLICADOS>
      <ARTIGO-PUBLICADO>
        <DADOS-BASICOS-DO-ARTIGO TITULO-DO-ARTIGO="Artigo Um" ANO-DO-ARTIGO="2024"/>
        <DETALHAMENTO-DO-ARTIGO TITULO-DO-PERIODICO-OU-REVISTA="Revista X" ISSN="12345678"/>
        <AUTORES NOME-PARA-CITACAO="TESTE, P." ORDEM-DE-AUTORIA="1"/>
      </ARTIGO-PUBLICADO>
    </ARTIGOS-PUBLICADOS>
  </PRODUCAO-BIBLIOGRAFICA>
  <ATUACOES-PROFISSIONAIS>
    <PROJETOS-DE-PESQUISA>
      <PROJETO-DE-PESQUISA TITULO-DO-PROJETO="Projeto Alpha" ANO-INICIO="2023"
        SITUACAO="EM_ANDAMENTO" NATUREZA="PESQUISA"/>
    </PROJETOS-DE-PESQUISA>
  </ATUACOES-PROFISSIONAIS>
</CURRICULO-VITAE>
"""


def test_parse_lattes_date():
    assert _parse_lattes_date("15052026") == __import__("datetime").date(2026, 5, 15)
    assert _parse_lattes_date("") is None


def test_load_mini_xml_structure(tmp_path):
    xml_path = tmp_path / "1234567890123456.xml"
    xml_path.write_text(MINI_XML, encoding="iso-8859-1")
    root = _load_xml_root(xml_path)

    assert root.attrib["NUMERO-IDENTIFICADOR"] == "1234567890123456"
    assert len(root.findall(".//ARTIGO-PUBLICADO")) == 1
    assert len(root.findall(".//PROJETO-DE-PESQUISA")) == 1
    assert len(root.findall("FORMACAO-ACADEMICA-TITULACAO/DOUTORADO")) == 1

    art = root.find(".//DADOS-BASICOS-DO-ARTIGO")
    assert art is not None
    assert art.attrib["TITULO-DO-ARTIGO"] == "Artigo Um"

    resolved = resolve_xml_path_for_lattes_id(
        "1234567890123456", xml_dir=str(tmp_path)
    )
    assert resolved == xml_path


def test_extended_xml_structure(tmp_path):
    xml_path = tmp_path / "ext.xml"
    xml_path.write_text(EXTENDED_MINI_XML, encoding="iso-8859-1")
    root = _load_xml_root(xml_path)
    assert len(root.findall(".//ORIENTACAO")) == 1
    assert len(root.findall(".//PARTICIPACAO-EM-BANCA")) == 1
    assert len(root.findall(".//PARTICIPACAO-EM-EVENTO")) == 1
    assert len(root.findall(".//LIVRO-PUBLICADO-OU-ORGANIZADO")) == 1


def test_split_orientacao_citation():
    from app.services.lattes_xml_importer import _split_orientacao_citation

    raw = (
        "Maria Silva. Estudo de caso. 2020. Monografia. "
        "Orientador: Prof Teste."
    )
    parsed = _split_orientacao_citation(raw)
    assert parsed is not None
    assert parsed["nome"] == "Maria Silva"
    assert parsed["titulo"] == "Estudo de caso"


def test_should_skip_formacao_logic():
    from app.services.extraction_registry import resolve_extraction_profile
    from app.services.lattes_xml_importer import should_skip_section_ai
    from unittest.mock import MagicMock

    section = MagicMock()
    section.curriculo_upload_id = "upload-1"
    section.nome_secao = "Formação acadêmica/titulação"
    assert resolve_extraction_profile(section.nome_secao) == "formacao"

    session = MagicMock()
    session.exec.return_value.all.return_value = [MagicMock()]

    assert should_skip_section_ai(session, section) is True

    section.nome_secao = "Orientações e supervisões"
    assert should_skip_section_ai(session, section) is True
