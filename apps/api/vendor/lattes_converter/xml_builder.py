from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.dom import minidom

from .html_parser import CurriculumHTML


def _sub(parent: ET.Element, tag: str, attrs: dict | None = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if attrs:
        for key, value in attrs.items():
            if value is not None and value != "":
                el.set(key, str(value))
    return el


def _empty_attrs(**kwargs: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in kwargs.items():
        attr = key.replace("_", "-")
        out[attr] = "" if value is None else str(value)
    return out


def build_xml(cv: CurriculumHTML) -> ET.ElementTree:
    root = ET.Element(
        "CURRICULO-VITAE",
        {
            "NUMERO-IDENTIFICADOR": cv.lattes_id,
            "DATA-ATUALIZACAO": cv.data_atualizacao,
        },
    )

    dados = _sub(
        root,
        "DADOS-GERAIS",
        _empty_attrs(
            NOME_COMPLETO=cv.nome_completo,
            NOME_EM_CITACOES_BIBLIOGRAFICAS=cv.citacoes_bibliograficas,
            PAIS_DE_NACIONALIDADE=cv.pais_nacionalidade or "Brasil",
            SIGLA_PAIS_NACIONALIDADE="BRA" if (cv.pais_nacionalidade or "Brasil").lower().startswith("brasil") else "",
            ORCID_ID=cv.orcid,
        ),
    )
    _sub(dados, "RESUMO-CV", {"TEXTO-RESUMO-CV-RH": cv.resumo})

    if cv.endereco_profissional:
        end = _sub(dados, "ENDERECO", {"FLAG_DE_AGENCIA_FOMENTO": "NAO", "FLAG_DE_AGENCIA_DE_ESTAGIO": "NAO"})
        _sub(
            end,
            "ENDERECO-PROFISSIONAL",
            _empty_attrs(
                INSTITUICAO_PROFISSIONAL=_extract_institution_from_address(cv.endereco_profissional),
                ENDERECO_COMPLETO=cv.endereco_profissional,
            ),
        )

    if cv.formacao_academica:
        fac = _sub(root, "FORMACAO-ACADEMICA-TITULACAO")
        for i, item in enumerate(cv.formacao_academica, start=1):
            _append_formacao(fac, item, sequencia=str(i))

    if cv.formacao_complementar:
        fcomp = _sub(root, "FORMACAO-COMPLEMENTAR")
        for i, item in enumerate(cv.formacao_complementar, start=1):
            _append_formacao_complementar(fcomp, item, sequencia=str(i))

    if cv.idiomas:
        idiomas = _sub(dados, "IDIOMAS")
        for item in cv.idiomas:
            _sub(
                idiomas,
                "IDIOMA",
                _empty_attrs(
                    IDIOMA=item["idioma"],
                    PROVA_DE_CONHECIMENTO=item.get("prova", ""),
                ),
            )

    if cv.artigos:
        prod = _sub(root, "PRODUCAO-BIBLIOGRAFICA")
        artigos = _sub(prod, "ARTIGOS-PUBLICADOS")
        for art in cv.artigos:
            _append_artigo(artigos, art)

    if cv.projetos:
        atuacoes = _sub(root, "ATUACOES-PROFISSIONAIS")
        projetos = _sub(atuacoes, "PROJETOS-DE-PESQUISA")
        for i, proj in enumerate(cv.projetos, start=1):
            _append_projeto(projetos, proj, sequencia=str(i))

    if cv.livros or cv.capitulos:
        prod = root.find("PRODUCAO-BIBLIOGRAFICA")
        if prod is None:
            prod = _sub(root, "PRODUCAO-BIBLIOGRAFICA")
        if cv.livros:
            livros_el = _sub(prod, "LIVROS-PUBLICADOS-OU-ORGANIZADOS")
            for i, liv in enumerate(cv.livros, start=1):
                _append_livro(livros_el, liv, str(i))
        if cv.capitulos:
            caps_el = _sub(prod, "CAPITULOS-DE-LIVROS-PUBLICADOS")
            for i, cap in enumerate(cv.capitulos, start=1):
                _append_capitulo(caps_el, cap, str(i))

    if cv.orientacoes:
        oc = _sub(root, "ORIENTACOES-CONCLUIDAS")
        for i, ori in enumerate(cv.orientacoes, start=1):
            _append_orientacao(oc, ori, str(i))

    if cv.bancas:
        bancas_root = _sub(root, "PARTICIPACAO-EM-BANCA-TRABALHOS-CONCLUSAO")
        for i, b in enumerate(cv.bancas, start=1):
            _append_banca(bancas_root, b, str(i))

    if cv.eventos:
        ev_root = _sub(root, "PARTICIPACAO-EM-EVENTOS-CONGRESSOS")
        for i, ev in enumerate(cv.eventos, start=1):
            _append_evento(ev_root, ev, str(i))

    return ET.ElementTree(root)


def _extract_institution_from_address(text: str) -> str:
    first = text.split("\n")[0] if text else ""
    if "," in first:
        return first.split(",")[0].strip()
    return first.strip()


def _append_formacao(parent: ET.Element, item: dict, sequencia: str) -> None:
    tag = item["nivel"] if item["nivel"] != "OUTRA" else "GRADUACAO"
    attrs = _empty_attrs(
        SEQUENCIA_FORMACAO=sequencia,
        NIVEL=_nivel_code(item["nivel"]),
        CODIGO_INSTITUICAO="",
        NOME_INSTITUICAO=item["nome_instituicao"],
        NOME_ORGAO="",
        CODIGO_ORGAO="",
        CODIGO_CURSO="",
        NOME_CURSO=item["nome_curso"] or item["nivel_line"],
        STATUS_DO_CURSO=item["status"],
        ANO_DE_INICIO=item["ano_inicio"],
        ANO_DE_CONCLUSAO=item["ano_fim"],
        TITULO_DO_TRABALHO_DE_CONCLUSAO_DE_CURSO=item["titulo"],
        NOME_DO_ORIENTADOR=item["orientador_nome"],
        NUMERO_ID_ORIENTADOR=item["orientador_id"],
        FLAG_BOLSA="SIM" if item["bolsista"] else "NAO",
        NOME_AGENCIA=item["agencia"],
        CODIGO_AGENCIA_FINANCIADORA="",
    )
    _sub(parent, tag, attrs)


def _nivel_code(nivel: str) -> str:
    return {
        "DOUTORADO": "4",
        "MESTRADO": "3",
        "GRADUACAO": "1",
        "ESPECIALIZACAO": "2",
    }.get(nivel, "1")


def _append_formacao_complementar(parent: ET.Element, item: dict, sequencia: str) -> None:
    _sub(
        parent,
        "FORMACAO-COMPLEMENTAR-OU-ATUALIZACAO",
        _empty_attrs(
            SEQUENCIA_FORMACAO=sequencia,
            TIPO="CURSO_DE_CURTA_DURACAO",
            TITULO=item["nivel_line"],
            ANO_DE_INICIO=item["ano_inicio"],
            ANO_DE_FIM=item["ano_fim"],
            NOME_INSTITUICAO=item["nome_instituicao"],
            CARGA_HORARIA=item.get("carga_horaria", ""),
            CODIGO_INSTITUICAO="",
            NOME_DO_ORIENTADOR="",
            FLAG_BOLSA="NAO",
        ),
    )


def _append_artigo(parent: ET.Element, art: dict) -> None:
    seq = art.get("sequencia", "")
    artigo = _sub(parent, "ARTIGO-PUBLICADO", {"SEQUENCIA-PRODUCAO": seq, "ORDEM-IMPORTANCIA": ""})
    _sub(
        artigo,
        "DADOS-BASICOS-DO-ARTIGO",
        _empty_attrs(
            NATUREZA="COMPLETO",
            TITULO_DO_ARTIGO=art["titulo"],
            ANO_DO_ARTIGO=art["ano"],
            PAIS_DE_PUBLICACAO="",
            IDIOMA="",
            MEIO_DE_DIVULGACAO="MEIO_DIGITAL",
            FLAG_RELEVANCIA="SIM" if art["relevante"] else "NAO",
            DOI=art["doi"],
            FLAG_DIVULGACAO_CIENTIFICA="NAO",
        ),
    )
    _sub(
        artigo,
        "DETALHAMENTO-DO-ARTIGO",
        _empty_attrs(
            TITULO_DO_PERIODICO_OU_REVISTA=art["periodico"],
            ISSN=art["issn"],
            VOLUME=art["volume"],
            FASCICULO="",
            SERIE="",
            PAGINA_INICIAL=art["pagina_inicial"],
            PAGINA_FINAL=art["pagina_final"],
            LOCAL_DE_PUBLICACAO="",
        ),
    )
    for autor in art.get("autores", []):
        _sub(
            artigo,
            "AUTORES",
            _empty_attrs(
                NOME_COMPLETO_DO_AUTOR=autor["nome_completo"],
                NOME_PARA_CITACAO=autor["nome_citacao"],
                ORDEM_DE_AUTORIA=autor["ordem"],
                NRO_ID_CNPQ=autor.get("lattes_id", ""),
            ),
        )


def _append_projeto(parent: ET.Element, proj: dict, sequencia: str) -> None:
    inicio, fim = _split_period(proj.get("periodo", ""))
    projeto = _sub(
        parent,
        "PROJETO-DE-PESQUISA",
        {
            "SEQUENCIA-PRODUCAO": sequencia,
            "TITULO-DO-PROJETO": proj["titulo"],
            "ANO-INICIO": inicio,
            "ANO-FIM": fim,
            "SITUACAO": "EM_ANDAMENTO" if "atual" in proj.get("periodo", "").lower() else "CONCLUIDO",
            "NATUREZA": "PESQUISA",
        },
    )
    if proj.get("descricao"):
        _sub(projeto, "DESCRICAO-DO-PROJETO", {"DESCRICAO-DO-PROJETO": proj["descricao"]})


def _append_livro(parent: ET.Element, liv: dict, sequencia: str) -> None:
    el = _sub(
        parent,
        "LIVRO-PUBLICADO-OU-ORGANIZADO",
        {"SEQUENCIA-PRODUCAO": sequencia},
    )
    _sub(
        el,
        "DADOS-BASICOS-DO-LIVRO",
        _empty_attrs(
            TITULO_DO_LIVRO=liv["titulo"],
            ANO=liv.get("ano", ""),
            NATUREZA="LIVRO",
        ),
    )
    if liv.get("autores"):
        _sub(
            el,
            "AUTORES",
            _empty_attrs(NOME_PARA_CITACAO=liv["autores"], ORDEM_DE_AUTORIA="1"),
        )


def _append_capitulo(parent: ET.Element, cap: dict, sequencia: str) -> None:
    el = _sub(
        parent,
        "CAPITULO-DE-LIVRO-PUBLICADO",
        {"SEQUENCIA-PRODUCAO": sequencia},
    )
    _sub(
        el,
        "DADOS-BASICOS-DO-CAPITULO",
        _empty_attrs(
            TITULO_DO_CAPITULO_DO_LIVRO=cap["titulo"],
            ANO=cap.get("ano", ""),
        ),
    )
    if cap.get("veiculo"):
        _sub(
            el,
            "DETALHAMENTO-DO-CAPITULO",
            _empty_attrs(TITULO_DO_LIVRO=cap["veiculo"]),
        )


def _append_orientacao(parent: ET.Element, ori: dict, sequencia: str) -> None:
    _sub(
        parent,
        "ORIENTACAO",
        {
            "SEQUENCIA-PRODUCAO": sequencia,
            "TIPO": ori.get("tipo", "outra"),
            "STATUS": ori.get("status", "concluida"),
            "NOME-ORIENTANDO": ori.get("nome_orientando", ""),
            "TITULO-DO-TRABALHO": ori.get("titulo_trabalho", ""),
            "ANO-INICIO": ori.get("ano_inicio", ""),
            "ANO-CONCLUSAO": ori.get("ano_conclusao", ""),
            "NOME-INSTITUICAO": ori.get("instituicao", ""),
        },
    )


def _append_banca(parent: ET.Element, banca: dict, sequencia: str) -> None:
    _sub(
        parent,
        "PARTICIPACAO-EM-BANCA",
        {
            "SEQUENCIA-PRODUCAO": sequencia,
            "TIPO": banca.get("tipo", "outra"),
            "NIVEL": banca.get("nivel", "outro"),
            "NOME-CANDIDATO": banca.get("nome_candidato", ""),
            "TITULO-DO-TRABALHO": banca.get("titulo_trabalho", ""),
            "ANO": banca.get("ano", ""),
        },
    )


def _append_evento(parent: ET.Element, ev: dict, sequencia: str) -> None:
    _sub(
        parent,
        "PARTICIPACAO-EM-EVENTO",
        {
            "SEQUENCIA-PRODUCAO": sequencia,
            "NOME-DO-EVENTO": ev.get("nome_evento", ""),
            "ANO": ev.get("ano", ""),
            "TIPO-PARTICIPACAO": ev.get("tipo_participacao", ""),
            "EH-ORGANIZACAO": "SIM" if ev.get("eh_organizacao") else "NAO",
        },
    )


def _split_period(period: str) -> tuple[str, str]:
    nums = __import__("re").findall(r"\d{4}", period)
    if not nums:
        return "", ""
    if len(nums) == 1:
        return nums[0], ""
    return nums[0], nums[1]


def tree_to_string(tree: ET.ElementTree) -> str:
    xml_bytes = ET.tostring(tree.getroot(), encoding="iso-8859-1")
    parsed = minidom.parseString(xml_bytes)
    # minidom adds xml declaration; keep ISO-8859-1
    rough = parsed.toprettyxml(indent="", encoding="iso-8859-1")
    if isinstance(rough, bytes):
        text = rough.decode("iso-8859-1")
    else:
        text = rough
    # compact like Lattes export (single line optional) - keep readable single line root
    lines = [ln for ln in text.splitlines() if ln.strip()]
    header = '<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>'
    body = "".join(lines[1:]) if lines and lines[0].startswith("<?xml") else "".join(lines)
    return header + body
