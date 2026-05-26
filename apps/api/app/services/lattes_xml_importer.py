"""Importa currículo Lattes a partir de XML (formato CNPq / lattes-xml)."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import and_
from sqlmodel import Session, select

from app.config import settings
from app.models.core import Professor
from app.models.data import (
    Banca,
    CurriculoUpload,
    Evento,
    FormacaoAcademica,
    Financiamento,
    Orientacao,
    PdfSection,
    PerfilLattes,
    Producao,
    Projeto,
)
from app.models.enums import (
    ConfiancaIA,
    FonteDado,
    NivelBanca,
    NivelFormacao,
    PapelBanca,
    PapelOrientacao,
    StatusOrientacao,
    StatusValidacao,
    TipoBanca,
    TipoFinanciamento,
    TipoOrientacao,
    TipoProjeto,
)
from app.services.ai_extractor import _update_professor_titulacao
from app.services.ai_response_normalizer import coerce_enum_value
from app.services.dedupe import (
    evento_already_exists,
    orientacao_already_exists,
    producao_already_exists,
    projeto_already_exists,
)
from app.services.extraction_registry import (
    resolve_extraction_profile,
    should_extract_producoes,
)
from app.services.professor_lookup import normalize_lattes_id

logger = logging.getLogger("ppgcomdata.lattes_xml")

_XML_SOURCE = FonteDado.XML_LATTES
_XML_CONF = ConfiancaIA.ALTA

_FORMACAO_TAGS: dict[str, NivelFormacao] = {
    "DOUTORADO": NivelFormacao.DOUTORADO,
    "MESTRADO": NivelFormacao.MESTRADO,
    "GRADUACAO": NivelFormacao.GRADUACAO,
    "POS-DOUTORADO": NivelFormacao.POS_DOUTORADO,
    "ESPECIALIZACAO": NivelFormacao.ESPECIALIZACAO,
}


def resolve_xml_path_for_lattes_id(lattes_id: str, xml_dir: Optional[str] = None) -> Optional[Path]:
    lid = normalize_lattes_id(lattes_id)
    if not lid:
        return None
    base = Path(xml_dir or settings.LATTES_XML_DIR or "")
    if not base.is_dir():
        return None
    candidate = base / f"{lid}.xml"
    return candidate if candidate.is_file() else None


def resolve_xml_path_for_upload(
    session: Session,
    upload_id: str,
    xml_dir: Optional[str] = None,
) -> Optional[Path]:
    upload = session.get(CurriculoUpload, upload_id)
    if not upload:
        return None

    from app.services.lattes_curriculo_import import resolve_xml_path_for_upload_record

    stored = resolve_xml_path_for_upload_record(upload)
    if stored and stored.is_file():
        return stored

    prof = session.get(Professor, upload.professor_id)
    if not prof or not prof.id_lattes:
        return None
    return resolve_xml_path_for_lattes_id(prof.id_lattes, xml_dir=xml_dir)


def _attr(el: ET.Element, name: str, default: str = "") -> str:
    return (el.attrib.get(name) or default).strip()


def _find_first(root: ET.Element, *paths: str) -> Optional[ET.Element]:
    for path in paths:
        el = root.find(path)
        if el is not None:
            return el
    return None


def _find_child_by_prefix(parent: ET.Element, prefix: str) -> Optional[ET.Element]:
    for child in parent:
        if child.tag.startswith(prefix):
            return child
    return parent.find(f".//{prefix}")


def _offline_orientacao_tipo(tag: str, natureza: str = "") -> TipoOrientacao:
    tag_u = tag.upper()
    nat_u = natureza.upper()
    if "MESTRADO" in tag_u:
        return TipoOrientacao.MESTRADO
    if "DOUTORADO" in tag_u and "POS" not in tag_u:
        return TipoOrientacao.DOUTORADO
    if "POS-DOUTORADO" in tag_u or "POS_DOUTORADO" in tag_u:
        return TipoOrientacao.POS_DOUTORADO
    if "GRADUACAO" in tag_u or "TCC" in nat_u or "MONOGRAFIA" in nat_u:
        return TipoOrientacao.TCC
    return TipoOrientacao.OUTRA


def _int_or_none(value: str) -> Optional[int]:
    value = (value or "").strip()
    if not value or not value.isdigit():
        return None
    return int(value)


def _parse_lattes_date(value: str) -> Optional[date]:
    """DATA-ATUALIZACAO no XML: DDMMYYYY."""
    value = re.sub(r"\D", "", value or "")
    if len(value) != 8:
        return None
    try:
        day, month, year = int(value[:2]), int(value[2:4]), int(value[4:8])
        return date(year, month, day)
    except ValueError:
        return None


def _situacao_projeto(raw: str) -> str:
    mapping = {
        "EM_ANDAMENTO": "em andamento",
        "CONCLUIDO": "concluído",
        "FINALIZADO": "concluído",
    }
    return mapping.get((raw or "").upper(), raw or "")


def _trecho_xml(tag: str, **attrs: str) -> str:
    parts = [f"{k}={v}" for k, v in attrs.items() if v]
    return f"<{tag} {' '.join(parts)}>" if parts else f"<{tag}>"


def _load_xml_root(path: Path) -> ET.Element:
    raw = path.read_bytes()
    for encoding in ("iso-8859-1", "windows-1252", "utf-8"):
        try:
            return ET.fromstring(raw.decode(encoding))
        except UnicodeDecodeError:
            continue
    return ET.fromstring(raw.decode("utf-8", errors="replace"))


def _count_xml_entities(session: Session, upload_id: str, model: type) -> int:
    col = model.__table__.c.get("curriculo_upload_id")
    if col is None:
        return 0
    stmt = select(model).where(
        and_(col == upload_id, model.fonte_dado == _XML_SOURCE)  # type: ignore[attr-defined]
    )
    return len(session.exec(stmt).all())


def _count_xml_producoes(session: Session, upload_id: str, tipo: str) -> int:
    stmt = select(Producao).where(
        and_(
            Producao.curriculo_upload_id == upload_id,
            Producao.fonte_dado == _XML_SOURCE,
            Producao.tipo == tipo,
        )
    )
    return len(session.exec(stmt).all())


def _coerce_orientacao_tipo(raw: str) -> TipoOrientacao:
    return TipoOrientacao(
        coerce_enum_value(raw, TipoOrientacao, default=TipoOrientacao.OUTRA)
    )


def _coerce_orientacao_status(raw: str) -> StatusOrientacao:
    key = (raw or "").lower().replace("-", "_")
    if key in ("em_andamento", "andamento"):
        return StatusOrientacao.EM_ANDAMENTO
    return StatusOrientacao.CONCLUIDA


def _coerce_banca_tipo(raw: str) -> TipoBanca:
    return TipoBanca(coerce_enum_value(raw, TipoBanca, default=TipoBanca.OUTRA))


def _coerce_banca_nivel(raw: str) -> NivelBanca:
    key = (raw or "").lower()
    if key == "graduacao":
        return NivelBanca.OUTRO
    return NivelBanca(coerce_enum_value(raw, NivelBanca, default=NivelBanca.OUTRO))


def should_skip_section_ai(session: Session, section: PdfSection) -> bool:
    """Pula IA quando o XML já preencheu o perfil da seção."""
    upload_id = section.curriculo_upload_id
    if not upload_id:
        return False

    profile = resolve_extraction_profile(section.nome_secao)
    nome = (section.nome_secao or "").lower()

    if profile == "formacao" and _count_xml_entities(session, upload_id, FormacaoAcademica) > 0:
        return True
    if profile == "perfil" and _count_xml_entities(session, upload_id, PerfilLattes) > 0:
        return True
    if profile == "orientacoes":
        return _count_xml_entities(session, upload_id, Orientacao) > 0
    if profile == "bancas":
        return _count_xml_entities(session, upload_id, Banca) > 0
    if profile == "padrao":
        if should_extract_producoes(section.nome_secao):
            if "livro" in nome and "capítulo" not in nome and "capitulo" not in nome:
                return _count_xml_producoes(session, upload_id, "livro") > 0
            if "capítulo" in nome or "capitulo" in nome:
                return _count_xml_producoes(session, upload_id, "capitulo") > 0
            if "artigo" in nome:
                return _count_xml_producoes(session, upload_id, "artigo") > 0
            return _count_xml_entities(session, upload_id, Producao) > 0
        if "projeto" in nome:
            return _count_xml_entities(session, upload_id, Projeto) > 0
        if "evento" in nome or "participação" in nome or "participacao" in nome:
            return _count_xml_entities(session, upload_id, Evento) > 0
        if "organização" in nome or "organizacao" in nome:
            return _count_xml_entities(session, upload_id, Evento) > 0
    return False


def import_lattes_xml(
    session: Session,
    upload_id: str,
    xml_path: str | Path,
) -> dict[str, Any]:
    """Persiste dados estruturados do XML no upload indicado."""
    path = Path(xml_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))

    upload = session.get(CurriculoUpload, upload_id)
    if not upload:
        raise ValueError(f"Upload {upload_id} não encontrado.")

    root = _load_xml_root(path)
    prof = session.get(Professor, upload.professor_id)
    if not prof:
        raise ValueError(f"Professor {upload.professor_id} não encontrado.")

    lattes_id = _attr(root, "NUMERO-IDENTIFICADOR")
    if lattes_id and not prof.id_lattes:
        prof.id_lattes = lattes_id
        session.add(prof)

    metrics: dict[str, int] = {
        "perfis_extraidos": 0,
        "formacoes_extraidas": 0,
        "producoes_extraidas": 0,
        "projetos_extraidos": 0,
        "financiamentos_extraidos": 0,
        "orientacoes_extraidas": 0,
        "bancas_extraidas": 0,
        "eventos_extraidos": 0,
    }

    dados = root.find("DADOS-GERAIS")
    if dados is not None:
        metrics["perfis_extraidos"] += _import_perfil(session, upload, prof, root, dados)

    formacao_root = _find_first(
        root,
        "FORMACAO-ACADEMICA-TITULACAO",
        "DADOS-GERAIS/FORMACAO-ACADEMICA-TITULACAO",
    )
    if formacao_root is not None:
        metrics["formacoes_extraidas"] += _import_formacoes(
            session, upload, formacao_root
        )

    biblio = root.find("PRODUCAO-BIBLIOGRAFICA")
    if biblio is not None:
        metrics["producoes_extraidas"] += _import_artigos(session, upload, biblio)
        metrics["producoes_extraidas"] += _import_livros_capitulos(session, upload, biblio)

    orient_root = _find_first(
        root,
        "ORIENTACOES-CONCLUIDAS",
        "OUTRA-PRODUCAO/ORIENTACOES-CONCLUIDAS",
    )
    if orient_root is not None:
        metrics["orientacoes_extraidas"] += _import_orientacoes(session, upload, orient_root)

    bancas_root = _find_first(
        root,
        "PARTICIPACAO-EM-BANCA-TRABALHOS-CONCLUSAO",
        "DADOS-COMPLEMENTARES/PARTICIPACAO-EM-BANCA-TRABALHOS-CONCLUSAO",
        "OUTRA-PRODUCAO/PARTICIPACAO-EM-BANCA-TRABALHOS-CONCLUSAO",
    )
    if bancas_root is not None:
        metrics["bancas_extraidas"] += _import_bancas(session, upload, bancas_root)

    eventos_root = _find_first(
        root,
        "PARTICIPACAO-EM-EVENTOS-CONGRESSOS",
        "DADOS-COMPLEMENTARES/PARTICIPACAO-EM-EVENTOS-CONGRESSOS",
    )
    if eventos_root is not None:
        metrics["eventos_extraidos"] += _import_eventos(session, upload, eventos_root)

    atuacoes = _find_first(
        root,
        "ATUACOES-PROFISSIONAIS",
        "DADOS-GERAIS/ATUACOES-PROFISSIONAIS",
    )
    if atuacoes is not None:
        metrics["projetos_extraidos"] += _import_projetos(session, upload, atuacoes)
        metrics["financiamentos_extraidos"] += _import_financiamentos_formacao(
            session, upload, formacao_root
        )

    _update_professor_titulacao(session, upload.professor_id)
    parsed_date = _parse_lattes_date(_attr(root, "DATA-ATUALIZACAO"))
    if prof and parsed_date:
        prof.data_ultima_atualizacao_lattes = parsed_date
        session.add(prof)

    session.commit()
    logger.info("XML importado %s → upload %s: %s", path.name, upload_id, metrics)
    return metrics


def _import_perfil(
    session: Session,
    upload: CurriculoUpload,
    prof: Professor,
    root: ET.Element,
    dados: ET.Element,
) -> int:
    resumo_el = dados.find("RESUMO-CV")
    resumo = _attr(resumo_el, "TEXTO-RESUMO-CV-RH") if resumo_el is not None else ""
    orcid = _attr(dados, "ORCID-ID")
    citacoes = _attr(dados, "NOME-EM-CITACOES-BIBLIOGRAFICAS")
    atualizacao = _parse_lattes_date(_attr(root, "DATA-ATUALIZACAO"))

    trecho = _trecho_xml(
        "DADOS-GERAIS",
        NOME=_attr(dados, "NOME-COMPLETO"),
        ORCID=orcid,
    )
    session.add(
        PerfilLattes(
            professor_id=upload.professor_id,
            curriculo_upload_id=upload.id,
            data_ultima_atualizacao=atualizacao,
            resumo_cv=resumo or None,
            nome_citacao=citacoes or None,
            link_orcid=orcid or None,
            fonte_dado=_XML_SOURCE,
            confianca_ia=_XML_CONF,
            trecho_original=trecho,
            status_validacao=StatusValidacao.PENDENTE,
        )
    )
    if citacoes:
        prof.nome_citacao = citacoes
    if atualizacao:
        prof.data_ultima_atualizacao_lattes = atualizacao
    session.add(prof)
    return 1


def _import_formacoes(
    session: Session,
    upload: CurriculoUpload,
    formacao_root: ET.Element,
) -> int:
    count = 0
    for tag, nivel in _FORMACAO_TAGS.items():
        for el in formacao_root.findall(tag):
            curso = _attr(el, "NOME-CURSO")
            inst = _attr(el, "NOME-INSTITUICAO")
            if not curso and not inst:
                continue
            session.add(
                FormacaoAcademica(
                    professor_id=upload.professor_id,
                    curriculo_upload_id=upload.id,
                    nivel=nivel,
                    curso=curso or None,
                    instituicao=inst or None,
                    ano_inicio=_int_or_none(_attr(el, "ANO-DE-INICIO")),
                    ano_fim=_int_or_none(_attr(el, "ANO-DE-CONCLUSAO")),
                    fonte_dado=_XML_SOURCE,
                    confianca_ia=_XML_CONF,
                    trecho_original=_trecho_xml(
                        tag,
                        CURSO=curso,
                        INSTITUICAO=inst,
                    ),
                    status_validacao=StatusValidacao.PENDENTE,
                )
            )
            count += 1
    return count


def _import_artigos(
    session: Session,
    upload: CurriculoUpload,
    biblio: ET.Element,
) -> int:
    count = 0
    for art in biblio.findall(".//ARTIGO-PUBLICADO"):
        basic = art.find("DADOS-BASICOS-DO-ARTIGO")
        det = art.find("DETALHAMENTO-DO-ARTIGO")
        if basic is None:
            continue
        titulo = _attr(basic, "TITULO-DO-ARTIGO")
        if not titulo:
            continue
        ano = _int_or_none(_attr(basic, "ANO-DO-ARTIGO"))
        if producao_already_exists(
            session,
            upload.professor_id,
            upload.id,
            titulo,
            ano,
            "artigo",
        ):
            continue

        autores = []
        primeiro_autor = None
        for autor in art.findall("AUTORES"):
            nome = _attr(autor, "NOME-PARA-CITACAO") or _attr(autor, "NOME-COMPLETO-DO-AUTOR")
            if nome:
                autores.append(nome)
            if _attr(autor, "ORDEM-DE-AUTORIA") == "1":
                primeiro_autor = True

        pag_ini = _attr(det, "PAGINA-INICIAL") if det is not None else ""
        pag_fim = _attr(det, "PAGINA-FINAL") if det is not None else ""
        paginas = pag_ini
        if pag_fim and pag_fim != pag_ini:
            paginas = f"{pag_ini}-{pag_fim}" if pag_ini else pag_fim

        session.add(
            Producao(
                professor_id=upload.professor_id,
                curriculo_upload_id=upload.id,
                tipo="artigo",
                titulo=titulo,
                ano=ano,
                veiculo=_attr(det, "TITULO-DO-PERIODICO-OU-REVISTA") if det is not None else None,
                doi=_attr(basic, "DOI") or None,
                issn=_attr(det, "ISSN") if det is not None else None,
                autores="; ".join(autores) if autores else None,
                volume=_attr(det, "VOLUME") if det is not None else None,
                paginas=paginas or None,
                eh_primeiro_autor=primeiro_autor,
                fonte_dado=_XML_SOURCE,
                confianca_ia=_XML_CONF,
                trecho_original=_trecho_xml(
                    "ARTIGO-PUBLICADO",
                    TITULO=titulo,
                    ANO=str(ano or ""),
                ),
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    return count


def _import_projetos(
    session: Session,
    upload: CurriculoUpload,
    atuacoes: ET.Element,
) -> int:
    count = 0
    for proj in atuacoes.findall(".//PROJETO-DE-PESQUISA"):
        titulo = _attr(proj, "TITULO-DO-PROJETO") or _attr(proj, "NOME-DO-PROJETO")
        if not titulo:
            continue
        ano_inicio = _int_or_none(_attr(proj, "ANO-INICIO"))
        if projeto_already_exists(
            session,
            upload.professor_id,
            upload.id,
            titulo,
            ano_inicio,
        ):
            continue
        desc_el = proj.find("DESCRICAO-DO-PROJETO")
        descricao = (
            _attr(desc_el, "DESCRICAO-DO-PROJETO")
            if desc_el is not None
            else _attr(proj, "DESCRICAO-DO-PROJETO")
        )
        natureza = _attr(proj, "NATUREZA").upper()
        tipo = TipoProjeto.PESQUISA
        if natureza == "EXTENSAO":
            tipo = TipoProjeto.EXTENSAO
        elif natureza == "DESENVOLVIMENTO":
            tipo = TipoProjeto.DESENVOLVIMENTO

        session.add(
            Projeto(
                professor_id=upload.professor_id,
                curriculo_upload_id=upload.id,
                titulo=titulo,
                tipo=tipo,
                situacao=_situacao_projeto(_attr(proj, "SITUACAO")),
                ano_inicio=ano_inicio,
                ano_fim=_int_or_none(_attr(proj, "ANO-FIM")),
                descricao=descricao or None,
                financiamento_mencionado=False,
                fonte_dado=_XML_SOURCE,
                confianca_ia=_XML_CONF,
                trecho_original=_trecho_xml("PROJETO-DE-PESQUISA", TITULO=titulo),
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    return count


def _import_livros_capitulos(
    session: Session,
    upload: CurriculoUpload,
    biblio: ET.Element,
) -> int:
    count = 0
    for tag, tipo in (
        ("LIVRO-PUBLICADO-OU-ORGANIZADO", "livro"),
        ("CAPITULO-DE-LIVRO-PUBLICADO", "capitulo"),
    ):
        basic_tag = (
            "DADOS-BASICOS-DO-LIVRO"
            if tipo == "livro"
            else "DADOS-BASICOS-DO-CAPITULO"
        )
        titulo_attr = (
            "TITULO-DO-LIVRO"
            if tipo == "livro"
            else "TITULO-DO-CAPITULO-DO-LIVRO"
        )
        for el in biblio.findall(f".//{tag}"):
            basic = el.find(basic_tag)
            if basic is None:
                continue
            titulo = _attr(basic, titulo_attr)
            if not titulo:
                continue
            ano = _int_or_none(_attr(basic, "ANO"))
            veiculo = None
            if tipo == "capitulo":
                det = el.find("DETALHAMENTO-DO-CAPITULO")
                if det is not None:
                    veiculo = _attr(det, "TITULO-DO-LIVRO") or None
            autores = None
            autor_el = el.find("AUTORES")
            if autor_el is not None:
                autores = _attr(autor_el, "NOME-PARA-CITACAO") or None
            if producao_already_exists(
                session,
                upload.professor_id,
                upload.id,
                titulo,
                ano,
                tipo,
            ):
                continue
            session.add(
                Producao(
                    professor_id=upload.professor_id,
                    curriculo_upload_id=upload.id,
                    tipo=tipo,
                    titulo=titulo,
                    ano=ano,
                    veiculo=veiculo,
                    autores=autores,
                    fonte_dado=_XML_SOURCE,
                    confianca_ia=_XML_CONF,
                    trecho_original=_trecho_xml(tag, TITULO=titulo, ANO=str(ano or "")),
                    status_validacao=StatusValidacao.PENDENTE,
                )
            )
            count += 1
    return count


def _import_orientacoes(
    session: Session,
    upload: CurriculoUpload,
    orient_root: ET.Element,
) -> int:
    count = 0
    for el in orient_root.findall("ORIENTACAO"):
        count += _add_orientacao_from_flat_xml(session, upload, el)

    for wrapper in orient_root:
        if wrapper.tag == "ORIENTACAO":
            continue
        basic = _find_child_by_prefix(wrapper, "DADOS-BASICOS")
        if basic is None:
            continue
        det = _find_child_by_prefix(wrapper, "DETALHAMENTO")
        titulo = _attr(basic, "TITULO") or _attr(basic, "TITULO-DO-TRABALHO")
        nome = _attr(det, "NOME-DO-ORIENTADO") if det is not None else ""
        if not nome and not titulo:
            continue
        ano_conclusao = _int_or_none(
            _attr(basic, "ANO-CONCLUSAO") or _attr(basic, "ANO")
        )
        if orientacao_already_exists(
            session,
            upload.professor_id,
            upload.id,
            nome,
            titulo,
            None,
        ):
            continue
        session.add(
            Orientacao(
                professor_id=upload.professor_id,
                curriculo_upload_id=upload.id,
                tipo=_offline_orientacao_tipo(wrapper.tag, _attr(basic, "NATUREZA")),
                status=StatusOrientacao.CONCLUIDA,
                nome_orientando=nome or None,
                titulo_trabalho=titulo or None,
                instituicao=_attr(det, "NOME-DA-INSTITUICAO") if det is not None else None,
                ano_inicio=None,
                ano_conclusao=ano_conclusao,
                papel=PapelOrientacao.ORIENTADOR,
                fonte_dado=_XML_SOURCE,
                confianca_ia=_XML_CONF,
                trecho_original=_trecho_xml(
                    wrapper.tag,
                    NOME=nome,
                    TITULO=titulo,
                ),
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    return count


def _add_orientacao_from_flat_xml(
    session: Session,
    upload: CurriculoUpload,
    el: ET.Element,
) -> int:
    nome = _attr(el, "NOME-ORIENTANDO")
    titulo = _attr(el, "TITULO-DO-TRABALHO")
    if nome and not titulo and re.search(r"\.\s+\d{4}\.", nome):
        parsed = _split_orientacao_citation(nome)
        if parsed:
            nome, titulo = parsed["nome"], parsed["titulo"]
    if not nome and not titulo:
        return 0
    ano_inicio = _int_or_none(_attr(el, "ANO-INICIO"))
    ano_conclusao = _int_or_none(_attr(el, "ANO-CONCLUSAO"))
    status = _coerce_orientacao_status(_attr(el, "STATUS"))
    if status == StatusOrientacao.CONCLUIDA and not ano_conclusao:
        ano_conclusao = ano_inicio
        ano_inicio = None
    if orientacao_already_exists(
        session,
        upload.professor_id,
        upload.id,
        nome,
        titulo,
        ano_inicio,
    ):
        return 0
    session.add(
        Orientacao(
            professor_id=upload.professor_id,
            curriculo_upload_id=upload.id,
            tipo=_coerce_orientacao_tipo(_attr(el, "TIPO")),
            status=status,
            nome_orientando=nome or None,
            titulo_trabalho=titulo or None,
            instituicao=_attr(el, "NOME-INSTITUICAO") or None,
            ano_inicio=ano_inicio,
            ano_conclusao=ano_conclusao,
            papel=PapelOrientacao.ORIENTADOR,
            fonte_dado=_XML_SOURCE,
            confianca_ia=_XML_CONF,
            trecho_original=_trecho_xml(
                "ORIENTACAO",
                NOME=nome,
                TITULO=titulo,
            ),
            status_validacao=StatusValidacao.PENDENTE,
        )
    )
    return 1


def _split_orientacao_citation(flat: str) -> dict[str, str] | None:
    text = re.sub(r"\s+", " ", flat).strip().rstrip(".")
    text = re.sub(r"\.\s*Orientador:\s*.+$", "", text, flags=re.I).strip()
    m = re.match(r"^(.+?)\.\s+(.+?)\.\s*\d{4}\.", text)
    if not m:
        return None
    return {"nome": m.group(1).strip(), "titulo": m.group(2).strip()}


def _import_bancas(
    session: Session,
    upload: CurriculoUpload,
    bancas_root: ET.Element,
) -> int:
    count = 0
    for el in bancas_root.findall("PARTICIPACAO-EM-BANCA"):
        candidato = _attr(el, "NOME-CANDIDATO")
        titulo = _attr(el, "TITULO-DO-TRABALHO")
        if not candidato and not titulo:
            continue
        session.add(
            Banca(
                professor_id=upload.professor_id,
                curriculo_upload_id=upload.id,
                tipo=_coerce_banca_tipo(_attr(el, "TIPO")),
                nivel=_coerce_banca_nivel(_attr(el, "NIVEL")),
                nome_candidato=candidato or None,
                titulo_trabalho=titulo or None,
                ano=_int_or_none(_attr(el, "ANO")),
                papel=PapelBanca.MEMBRO,
                fonte_dado=_XML_SOURCE,
                confianca_ia=_XML_CONF,
                trecho_original=_trecho_xml(
                    "PARTICIPACAO-EM-BANCA",
                    CANDIDATO=candidato,
                    TITULO=titulo,
                ),
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    return count


def _import_eventos(
    session: Session,
    upload: CurriculoUpload,
    eventos_root: ET.Element,
) -> int:
    count = 0
    for el in eventos_root.findall("PARTICIPACAO-EM-EVENTO"):
        count += _add_evento_from_flat_xml(session, upload, el)

    for el in eventos_root.findall("PARTICIPACAO-EM-CONGRESSO"):
        basic = _find_child_by_prefix(el, "DADOS-BASICOS")
        if basic is None:
            continue
        nome = _attr(basic, "TITULO") or _attr(basic, "NOME-DO-EVENTO")
        if not nome:
            continue
        ano = _int_or_none(_attr(basic, "ANO"))
        eh_org = _attr(basic, "FORMA-PARTICIPACAO").upper() == "ORGANIZADOR"
        if evento_already_exists(
            session,
            upload.professor_id,
            upload.id,
            nome,
            ano,
            eh_org,
        ):
            continue
        session.add(
            Evento(
                professor_id=upload.professor_id,
                curriculo_upload_id=upload.id,
                nome_evento=nome,
                ano=ano,
                tipo_participacao=_attr(basic, "TIPO-PARTICIPACAO") or None,
                eh_organizacao=eh_org,
                fonte_dado=_XML_SOURCE,
                confianca_ia=_XML_CONF,
                trecho_original=_trecho_xml("PARTICIPACAO-EM-CONGRESSO", NOME=nome),
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    return count


def _add_evento_from_flat_xml(
    session: Session,
    upload: CurriculoUpload,
    el: ET.Element,
) -> int:
    nome = _attr(el, "NOME-DO-EVENTO")
    if not nome:
        return 0
    ano = _int_or_none(_attr(el, "ANO"))
    eh_org = _attr(el, "EH-ORGANIZACAO").upper() == "SIM"
    if evento_already_exists(
        session,
        upload.professor_id,
        upload.id,
        nome,
        ano,
        eh_org,
    ):
        return 0
    session.add(
        Evento(
            professor_id=upload.professor_id,
            curriculo_upload_id=upload.id,
            nome_evento=nome,
            ano=ano,
            tipo_participacao=_attr(el, "TIPO-PARTICIPACAO") or None,
            eh_organizacao=eh_org,
            fonte_dado=_XML_SOURCE,
            confianca_ia=_XML_CONF,
            trecho_original=_trecho_xml("PARTICIPACAO-EM-EVENTO", NOME=nome),
            status_validacao=StatusValidacao.PENDENTE,
        )
    )
    return 1


def _import_financiamentos_formacao(
    session: Session,
    upload: CurriculoUpload,
    formacao_root: Optional[ET.Element],
) -> int:
    if formacao_root is None:
        return 0
    count = 0
    for tag in _FORMACAO_TAGS:
        for el in formacao_root.findall(tag):
            if _attr(el, "FLAG-BOLSA").upper() != "SIM":
                continue
            agencia = _attr(el, "NOME-AGENCIA")
            if not agencia:
                continue
            ano = _int_or_none(_attr(el, "ANO-DE-INICIO"))
            session.add(
                Financiamento(
                    professor_id=upload.professor_id,
                    tipo=TipoFinanciamento.BOLSA,
                    agencia=agencia,
                    ano=ano,
                    fonte_dado=_XML_SOURCE,
                    confianca=_XML_CONF,
                    trecho_original=_trecho_xml(tag, AGENCIA=agencia),
                    status_validacao=StatusValidacao.PENDENTE,
                )
            )
            count += 1
    return count


def import_lattes_xml_if_available(
    session: Session,
    upload_id: str,
    xml_dir: Optional[str] = None,
) -> dict[str, Any]:
    """Importa XML se existir arquivo para o id_lattes do docente."""
    path = resolve_xml_path_for_upload(session, upload_id, xml_dir=xml_dir)
    if not path:
        return {"xml_importado": False}
    metrics = import_lattes_xml(session, upload_id, path)
    metrics["xml_importado"] = True
    metrics["xml_arquivo"] = path.name
    return metrics


def mark_xml_covered_sections_extracted(session: Session, upload_id: str) -> int:
    """Marca seções cobertas pelo XML como já processadas (sem IA)."""
    sections = session.exec(
        select(PdfSection).where(PdfSection.curriculo_upload_id == upload_id)
    ).all()
    marked = 0
    for section in sections:
        if should_skip_section_ai(session, section):
            section.status_extracao = True
            session.add(section)
            marked += 1
    if marked:
        session.commit()
    return marked
