"""Heurísticas e persistência de grupos de pesquisa a partir do XML Lattes."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Optional

from sqlmodel import Session, select

from app.models.data import CurriculoUpload, GrupoPesquisaDocente
from app.models.enums import (
    ConfiancaIA,
    FonteDado,
    PapelGrupoPesquisa,
    StatusValidacao,
)
from app.services.dedupe import normalize_text_key

_GRUPO_TITLE_PATTERNS = (
    re.compile(r"grupo\s+de\s+(pesquisa|estudos)", re.I),
    re.compile(r"^grupo\s+(de\s+)?(pesquisa|estudos)", re.I),
    re.compile(r"laborat[oó]rio\s+de\s+pesquisa", re.I),
    re.compile(r"observat[oó]rio\s+de", re.I),
    re.compile(r"rede\s+de\s+grupos", re.I),
    re.compile(r"n[uú]cleo\s+de\s+pesquisa", re.I),
)

_DGP_IN_TEXT = re.compile(
    r"(?:dgp\.?cn?q\.?br[^\d]{0,40}|codigo\s+dgp|dgp\s*n[°ºo\.]*)\s*(\d{10,16})",
    re.I,
)
_DGP_PLAIN = re.compile(r"\b(\d{12,16})\b")


def is_lattes_projeto_grupo_pesquisa(
    titulo: str,
    natureza: str = "",
    descricao: str = "",
) -> bool:
    """
    Identifica projetos Lattes que representam vínculo em grupo CNPq.

    No currículo, grupos costumam ser cadastrados em Projetos → Outros tipos de projeto.
    """
    title = (titulo or "").strip()
    if not title:
        return False

    nat = (natureza or "").upper().strip()
    if nat in ("OUTRO", "OUTROS", "OUTRA"):
        return True

    for pattern in _GRUPO_TITLE_PATTERNS:
        if pattern.search(title):
            return True

    if re.search(r"grupo\s+de\s+pesquisa", title, re.I):
        return True

    desc = (descricao or "").lower()
    if "espelhogrupo" in desc or "dgp.cnpq" in desc:
        return True

    return False


def extract_codigo_dgp(titulo: str, descricao: str = "") -> Optional[str]:
    for text in (titulo, descricao):
        if not text:
            continue
        m = _DGP_IN_TEXT.search(text)
        if m:
            return m.group(1)
        m = _DGP_PLAIN.search(text)
        if m:
            return m.group(1)
    return None


def grupo_pesquisa_already_exists(
    session: Session,
    professor_id: str,
    nome_grupo: str,
) -> bool:
    key = normalize_text_key(nome_grupo)
    if not key:
        return False
    stmt = select(GrupoPesquisaDocente).where(
        GrupoPesquisaDocente.professor_id == professor_id
    )
    for row in session.exec(stmt).all():
        if normalize_text_key(row.nome_grupo) == key:
            return True
    return False


def _parse_grupo_from_projeto_element(
    proj: ET.Element,
    attr_fn,
    trecho_fn,
) -> Optional[dict]:
    titulo = attr_fn(proj, "TITULO-DO-PROJETO") or attr_fn(proj, "NOME-DO-PROJETO")
    if not titulo:
        return None

    desc_el = proj.find("DESCRICAO-DO-PROJETO")
    descricao = (
        attr_fn(desc_el, "DESCRICAO-DO-PROJETO")
        if desc_el is not None
        else attr_fn(proj, "DESCRICAO-DO-PROJETO")
    )

    if not is_lattes_projeto_grupo_pesquisa(
        titulo, attr_fn(proj, "NATUREZA"), descricao or ""
    ):
        return None

    instituicao = attr_fn(proj, "NOME-INSTITUICAO") or None
    linha = attr_fn(proj, "LINHA-DE-PESQUISA") or attr_fn(proj, "LINHA-TEMA") or None

    return {
        "nome_grupo": titulo.strip(),
        "codigo_dgp": extract_codigo_dgp(titulo, descricao or ""),
        "instituicao": instituicao,
        "linha_tematica": linha,
        "trecho_original": trecho_fn(
            "PROJETO-DE-PESQUISA-GRUPO",
            TITULO=titulo,
            NATUREZA=attr_fn(proj, "NATUREZA"),
        ),
    }


def import_grupos_from_atuacoes_xml(
    session: Session,
    upload: CurriculoUpload,
    atuacoes: ET.Element,
    *,
    attr_fn,
    trecho_fn,
    fonte: FonteDado,
    confianca: ConfiancaIA,
) -> int:
    """Extrai grupos de elementos PROJETO-DE-PESQUISA classificados como grupo."""
    count = 0
    for proj in atuacoes.findall(".//PROJETO-DE-PESQUISA"):
        parsed = _parse_grupo_from_projeto_element(proj, attr_fn, trecho_fn)
        if not parsed:
            continue
        if grupo_pesquisa_already_exists(
            session, upload.professor_id, parsed["nome_grupo"]
        ):
            continue
        session.add(
            GrupoPesquisaDocente(
                professor_id=upload.professor_id,
                curriculo_upload_id=upload.id,
                nome_grupo=parsed["nome_grupo"],
                codigo_dgp=parsed.get("codigo_dgp"),
                papel=PapelGrupoPesquisa.MEMBRO,
                linha_tematica=parsed.get("linha_tematica"),
                instituicao=parsed.get("instituicao"),
                fonte_dado=fonte,
                confianca_ia=confianca,
                trecho_original=parsed.get("trecho_original"),
                status_validacao=StatusValidacao.PENDENTE,
            )
        )
        count += 1
    return count
