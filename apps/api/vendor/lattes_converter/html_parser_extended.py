"""Seções adicionais do HTML Lattes: orientações, bancas, livros, capítulos, eventos."""

from __future__ import annotations

import re

from bs4 import Tag

from .html_parser import CurriculumHTML
from .utils import clean_text


def parse_extended_sections(cv: CurriculumHTML) -> None:
    _parse_livros_capitulos(cv)
    _parse_orientacoes(cv)
    _parse_bancas(cv)
    _parse_eventos(cv)


def _iter_transforms_between(
    soup,
    start_anchor: str,
    stop_anchors: tuple[str, ...],
) -> list[str]:
    start = soup.find("a", attrs={"name": start_anchor})
    if not start:
        return []
    texts: list[str] = []
    for el in start.find_all_next():
        if el.name == "a":
            name = el.get("name") or ""
            if name in stop_anchors:
                break
        if el.name == "span" and "transform" in (el.get("class") or []):
            text = clean_text(el.get_text("\n", strip=True))
            if len(text) > 20:
                texts.append(text)
    return texts


def _parse_livros_capitulos(cv: CurriculumHTML) -> None:
    anchor = cv.soup.find("a", attrs={"name": "LivrosCapitulos"})
    if not anchor:
        return
    mode: str | None = None
    for el in anchor.find_all_next():
        if el.name == "a" and el.get("name") in (
            "ProducaoTecnica",
            "Eventos",
            "EducacaoPopularizacaoCTA",
        ):
            break
        if el.name == "div" and "cita-artigos" in (el.get("class") or []):
            header = clean_text(el.get_text()).lower()
            if "capítulo" in header or "capitulo" in header:
                mode = "capitulo"
            elif "livro" in header:
                mode = "livro"
            continue
        if el.name == "span" and "transform" in (el.get("class") or []):
            text = clean_text(el.get_text(" ", strip=True))
            if len(text) < 25:
                continue
            effective_mode = mode
            if effective_mode is None:
                if " In: " in text or re.search(r"\bIn:\s", text, re.I):
                    effective_mode = "capitulo"
                elif re.search(r"\b\d+\s*ed\.\s", text, re.I) or "Editora " in text:
                    effective_mode = "livro"
                else:
                    continue
            item = _parse_producao_biblio_citation(text, effective_mode)
            if item:
                if effective_mode == "livro":
                    if not any(l["titulo"] == item["titulo"] for l in cv.livros):
                        cv.livros.append(item)
                elif effective_mode == "capitulo":
                    cv.capitulos.append(item)


def _parse_producao_biblio_citation(text: str, mode: str) -> dict | None:
    if mode == "capitulo" or " In: " in text or " in: " in text.lower():
        parts = re.split(r"\s+In:\s+", text, maxsplit=1, flags=re.I)
        body = parts[0]
        veiculo = parts[1] if len(parts) > 1 else ""
        titulo_m = re.search(r"\.\s+([^.;]+?)\s*\.?\s*(?:\d|$)", body)
        titulo = clean_text(titulo_m.group(1)) if titulo_m else clean_text(body[:120])
    else:
        veiculo = ""
        titulo_m = re.search(
            r"(?:NASCIMENTO|SILVA|REIS|BUENO)[^.]*\.\s+(.+?)\s*\d+\s*ed\.",
            text,
            re.I,
        )
        if not titulo_m:
            titulo_m = re.search(r"\.\s+([^.;]{10,}?)\s*\.?\s*\d", text)
        titulo = clean_text(titulo_m.group(1)) if titulo_m else ""
    if not titulo:
        return None
    ano_m = re.search(r"\b(19|20)\d{2}\b", text)
    autores_m = re.match(r"^(.+?)\.\s+", text)
    return {
        "titulo": titulo,
        "ano": ano_m.group(0) if ano_m else "",
        "veiculo": clean_text(veiculo)[:500] if veiculo else None,
        "autores": autores_m.group(1) if autores_m else None,
        "citacao": text[:800],
    }


def _parse_orientacoes(cv: CurriculumHTML) -> None:
    for anchor, status in (
        ("Orientacoesconcluidas", "concluida"),
        ("Orientacaoemandamento", "em_andamento"),
    ):
        for text in _iter_transforms_between(
            cv.soup,
            anchor,
            ("Orientacaoemandamento", "EducacaoPopularizacaoCTA", "Bancas", "Eventos"),
        ):
            if "participação em banca" in text.lower() or "participacao em banca" in text.lower():
                continue
            item = _parse_orientacao_text(text, status)
            if item:
                cv.orientacoes.append(item)


def _parse_orientacao_text(text: str, status: str) -> dict | None:
    flat = re.sub(r"\s+", " ", clean_text(text)).strip().rstrip(".")
    if not flat:
        return None
    flat = re.sub(r"\.\s*Orientador:\s*.+$", "", flat, flags=re.I).strip()

    nome = ""
    titulo = ""
    ano = ""
    rest = flat
    m = re.match(r"^(.+?)\.\s+(.+?)\.\s*(\d{4})\.\s*(.+)$", flat)
    if m:
        nome, titulo, ano, rest = m.group(1), m.group(2), m.group(3), m.group(4)
    else:
        lines = [clean_text(ln) for ln in text.split("\n") if clean_text(ln)]
        if not lines:
            return None
        nome = lines[0].rstrip(".")
        titulo = lines[1] if len(lines) > 1 else ""
        for line in lines[2:]:
            ym = re.match(r"^(\d{4})\.?$", line)
            if ym:
                ano = ym.group(1)
            else:
                rest = f"{rest} {line}".strip()

    tipo = "outra"
    instituicao = ""
    low = rest.lower()
    if "disserta" in low and "mestrado" in low:
        tipo = "mestrado"
    elif "mestrado" in low:
        tipo = "mestrado"
    elif "doutorado" in low:
        tipo = "doutorado"
    elif "monografia" in low or "trabalho de conclus" in low or "gradua" in low:
        tipo = "tcc"
    elif "inicia" in low and "cient" in low:
        tipo = "ic"
    elif "pós-doutorado" in low or "pos-doutorado" in low or "pos doutorado" in low:
        tipo = "pos_doutorado"
    inst_m = re.search(r"-\s*(.+?)(?:\.\s*|$)", rest)
    if inst_m:
        instituicao = inst_m.group(1).strip()

    if not nome and not titulo:
        return None
    return {
        "tipo": tipo,
        "status": status,
        "nome_orientando": nome,
        "titulo_trabalho": titulo,
        "ano_conclusao": ano,
        "ano_inicio": ano if status == "em_andamento" else "",
        "instituicao": instituicao,
        "trecho": text[:500],
    }


def _parse_bancas(cv: CurriculumHTML) -> None:
    for text in _iter_transforms_between(
        cv.soup,
        "Bancas",
        ("Orientacoesconcluidas", "EducacaoPopularizacaoCTA", "Eventos"),
    ):
        if "participação em banca" not in text.lower() and "participacao em banca" not in text.lower():
            continue
        item = _parse_banca_text(text)
        if item:
            cv.bancas.append(item)


def _parse_banca_text(text: str) -> dict | None:
    flat = re.sub(r"\s+", " ", text)
    m = re.search(
        r"Participa[cç][aã]o em banca de\s+(.+?)\.\s*(.+?)\.\s*(\d{4})",
        flat,
        re.I,
    )
    if not m:
        return None
    candidato = clean_text(m.group(1))
    titulo = clean_text(m.group(2))
    ano = m.group(3)
    nivel = "outro"
    tipo = "outra"
    low = flat.lower()
    if "mestrado" in low:
        nivel = "mestrado"
        tipo = "defesa"
    elif "doutorado" in low:
        nivel = "doutorado"
        tipo = "defesa"
    elif "qualifica" in low:
        tipo = "qualificacao"
    elif "gradua" in low or "tcc" in low:
        nivel = "graduacao"
        tipo = "defesa"
    return {
        "nome_candidato": candidato,
        "titulo_trabalho": titulo,
        "ano": ano,
        "tipo": tipo,
        "nivel": nivel,
        "trecho": flat[:500],
    }


def _parse_eventos(cv: CurriculumHTML) -> None:
    for anchor, eh_org in (("ParticipacaoEventos", False), ("OrganizacaoEventos", True)):
        for text in _iter_transforms_between(
            cv.soup,
            anchor,
            ("ProducaoTecnica", "EducacaoPopularizacaoCTA", "Bancas", "Orientacoesconcluidas"),
        ):
            item = _parse_evento_text(text, eh_org)
            if item:
                cv.eventos.append(item)


def _parse_evento_text(text: str, eh_organizacao: bool) -> dict | None:
    flat = clean_text(text)
    m = re.search(r"^(.+?)\s+(\d{4})\.\s*\(([^)]+)\)\s*\.?\s*$", flat)
    if not m:
        m = re.search(r"(.+?)\s+(\d{4})\.\s*\(([^)]+)\)", flat)
    if not m:
        return None
    nome = clean_text(m.group(1))
    if nome.startswith("SILVA,") or nome.startswith("NASCIMENTO,"):
        nome = re.sub(r"^[A-Z.,\s]+?\.\s*", "", nome)
    return {
        "nome_evento": nome[:300],
        "ano": m.group(2),
        "tipo_participacao": "organizador" if eh_organizacao else m.group(3).strip().lower(),
        "eh_organizacao": eh_organizacao,
        "trecho": flat[:400],
    }
