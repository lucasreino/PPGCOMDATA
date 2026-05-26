from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from .utils import clean_text, date_br_to_lattes, extract_lattes_id


@dataclass
class CurriculumHTML:
    soup: BeautifulSoup
    lattes_id: str = ""
    nome_completo: str = ""
    data_atualizacao: str = ""
    resumo: str = ""
    citacoes_bibliograficas: str = ""
    orcid: str = ""
    pais_nacionalidade: str = ""
    endereco_profissional: str = ""
    formacao_academica: list[dict] = field(default_factory=list)
    formacao_complementar: list[dict] = field(default_factory=list)
    artigos: list[dict] = field(default_factory=list)
    livros: list[dict] = field(default_factory=list)
    capitulos: list[dict] = field(default_factory=list)
    projetos: list[dict] = field(default_factory=list)
    idiomas: list[dict] = field(default_factory=list)
    orientacoes: list[dict] = field(default_factory=list)
    bancas: list[dict] = field(default_factory=list)
    eventos: list[dict] = field(default_factory=list)


def load_html(path: str | Path) -> CurriculumHTML:
    path = Path(path)
    raw = path.read_bytes()
    for encoding in ("windows-1252", "iso-8859-1", "utf-8"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            text = None
    if text is None:
        text = raw.decode("utf-8", errors="replace")

    soup = BeautifulSoup(text, "lxml")
    cv = CurriculumHTML(soup=soup)
    _parse_header(cv)
    _parse_identification(cv)
    _parse_address(cv)
    _parse_formacao_academica(cv)
    _parse_formacao_complementar(cv)
    _parse_artigos(cv)
    _parse_projetos(cv)
    _parse_idiomas(cv)
    from .html_parser_extended import parse_extended_sections

    parse_extended_sections(cv)
    return cv


def _parse_header(cv: CurriculumHTML) -> None:
    nome_el = cv.soup.select_one("h2.nome")
    if nome_el:
        cv.nome_completo = clean_text(nome_el.get_text())

    for li in cv.soup.select("ul.informacoes-autor li"):
        txt = li.get_text(" ", strip=True)
        if "ID Lattes" in txt:
            m = re.search(r"(\d{16})", txt)
            if m:
                cv.lattes_id = m.group(1)
        elif "atualiza" in txt.lower():
            m = re.search(r"(\d{2}/\d{2}/\d{4})", txt)
            if m:
                cv.data_atualizacao = date_br_to_lattes(m.group(1))

    resumo = cv.soup.select_one("p.resumo")
    if resumo:
        cv.resumo = clean_text(resumo.get_text(" ", strip=True))


def _section_after_anchor(soup: BeautifulSoup, anchor_name: str) -> Tag | None:
    anchor = soup.find("a", attrs={"name": anchor_name})
    if not anchor:
        return None
    wrapper = anchor.find_parent("div", class_="title-wrapper")
    return wrapper


def _parse_identification(cv: CurriculumHTML) -> None:
    wrapper = _section_after_anchor(cv.soup, "Identificacao")
    if not wrapper:
        return
    rows = wrapper.select("div.data-cell .layout-cell-3.text-align-right b")
    for label_el in rows:
        label = clean_text(label_el.get_text()).lower()
        value_cell = label_el.find_parent("div", class_="layout-cell-3")
        if not value_cell:
            continue
        content = value_cell.find_next_sibling("div", class_="layout-cell-9")
        if not content:
            continue
        value = clean_text(content.get_text(" ", strip=True))
        if "cita" in label and "bibliogr" in label:
            cv.citacoes_bibliograficas = value
        elif "orcid" in label:
            link = content.find("a", href=re.compile(r"orcid\.org"))
            cv.orcid = link["href"] if link else value
        elif "nacionalidade" in label:
            cv.pais_nacionalidade = value


def _parse_address(cv: CurriculumHTML) -> None:
    wrapper = _section_after_anchor(cv.soup, "Endereco")
    if not wrapper:
        return
    content_cells = wrapper.select("div.layout-cell-9 div.layout-cell-pad-5")
    if content_cells:
        cv.endereco_profissional = clean_text(content_cells[0].get_text("\n", strip=True))


def _parse_rows_in_section(wrapper: Tag) -> list[tuple[str, Tag]]:
    rows: list[tuple[str, Tag]] = []
    for date_el in wrapper.select("div.layout-cell-3.text-align-right > div.layout-cell-pad-5 > b"):
        date_label = clean_text(date_el.get_text())
        if not re.search(r"\d{4}", date_label):
            continue
        left = date_el.find_parent("div", class_="layout-cell-3")
        right = left.find_next_sibling("div", class_="layout-cell-9") if left else None
        if right:
            rows.append((date_label, right))
    return rows


def _parse_formacao_academica(cv: CurriculumHTML) -> None:
    wrapper = _section_after_anchor(cv.soup, "FormacaoAcademicaTitulacao")
    if not wrapper:
        return
    for date_label, content in _parse_rows_in_section(wrapper):
        cv.formacao_academica.append(_parse_formacao_block(date_label, content, complementar=False))


def _parse_formacao_complementar(cv: CurriculumHTML) -> None:
    wrapper = _section_after_anchor(cv.soup, "FormacaoComplementar")
    if not wrapper:
        return
    for date_label, content in _parse_rows_in_section(wrapper):
        cv.formacao_complementar.append(_parse_formacao_block(date_label, content, complementar=True))


def _parse_formacao_block(date_label: str, content: Tag, *, complementar: bool) -> dict:
    from .utils import field_after_label, parse_institution_line, parse_year_range

    lines = [ln.strip() for ln in content.get_text("\n", strip=True).split("\n") if ln.strip()]
    text = "\n".join(lines)
    start, end, status = parse_year_range(date_label)

    nivel_line = lines[0] if lines else ""
    nivel = _detect_nivel(nivel_line, complementar=complementar)

    inst_line = lines[1] if len(lines) > 1 else ""
    nome_inst, sigla_inst, pais = parse_institution_line(inst_line)

    orientador_nome = ""
    orientador_id = ""
    orientador_el = content.find("a", class_="icone-lattes")
    if orientador_el:
        orientador_id = extract_lattes_id(orientador_el.get("href"))
        orientador_nome = field_after_label(text, "Orientador").replace("Dr.", "").replace("Dra.", "").strip()

    item = {
        "nivel": nivel,
        "nivel_line": nivel_line,
        "ano_inicio": start,
        "ano_fim": end,
        "status": status,
        "nome_instituicao": nome_inst,
        "sigla_instituicao": sigla_inst,
        "pais": pais,
        "nome_curso": _extract_course_name(nivel_line),
        "titulo": field_after_label(text, "Título") or field_after_label(text, "Titulo"),
        "orientador_nome": orientador_nome,
        "orientador_id": orientador_id,
        "bolsista": "Bolsista do(a):" in text,
        "agencia": field_after_label(text, "Bolsista do(a)"),
        "carga_horaria": _extract_carga_horaria(nivel_line),
        "complementar": complementar,
    }
    return item


def _detect_nivel(line: str, *, complementar: bool) -> str:
    if complementar:
        return "FORMACAO-COMPLEMENTAR"
    low = line.lower()
    if "doutorado" in low:
        return "DOUTORADO"
    if "mestrado" in low:
        return "MESTRADO"
    if "gradua" in low:
        return "GRADUACAO"
    if "especializa" in low:
        return "ESPECIALIZACAO"
    if "ensino m" in low:
        return "ENSINO-MEDIO"
    if "ensino fundamental" in low:
        return "ENSINO-FUNDAMENTAL"
    return "OUTRA"


def _extract_course_name(line: str) -> str:
    m = re.search(r"(?:Doutorado|Mestrado|Graduação|Graduacao|Especialização|Especializacao) em (.+)", line, re.I)
    return clean_text(m.group(1)) if m else ""


def _extract_carga_horaria(line: str) -> str:
    m = re.search(r"Carga horária:\s*([^)]+)\)", line, re.I)
    return clean_text(m.group(1)) if m else ""


def _parse_artigos(cv: CurriculumHTML) -> None:
    from .utils import parse_cvuri

    for div in cv.soup.select("div.artigo-completo"):
        transform = div.select_one("span.transform")
        if not transform:
            continue

        citado = div.select_one("span.citado")
        cvuri = parse_cvuri(citado.get("cvuri") if citado else None)

        year_span = div.select_one("span[data-tipo-ordenacao='ano']")
        ano = year_span.get_text(strip=True) if year_span else ""

        doi_link = div.select_one("a.icone-doi")
        doi = ""
        if doi_link and doi_link.get("href"):
            doi = doi_link["href"].replace("http://dx.doi.org/", "").strip()

        titulo = cvuri.get("titulo", "")
        citation_text = _citation_plain_text(transform, titulo)
        autores = _parse_autores(transform, citation_text, titulo, cv.lattes_id, cv.nome_completo)

        volume = cvuri.get("volume", "")
        pagina = cvuri.get("paginaInicial", "")
        pagina_final = ""
        if "-" in pagina:
            parts = pagina.split("-", 1)
            pagina, pagina_final = parts[0], parts[1]

        if not ano:
            m = re.search(r",\s*(\d{4})\s*\.", citation_text)
            if m:
                ano = m.group(1)

        cv.artigos.append(
            {
                "sequencia": cvuri.get("sequencial", ""),
                "titulo": titulo or _guess_title(citation_text),
                "ano": ano,
                "doi": doi or cvuri.get("doi", ""),
                "issn": cvuri.get("issn", ""),
                "periodico": cvuri.get("nomePeriodico", ""),
                "volume": volume,
                "pagina_inicial": pagina,
                "pagina_final": pagina_final,
                "relevante": bool(div.select("img[src*='ico_relevante']")),
                "autores": autores,
                "citacao": citation_text,
            }
        )


def _citation_plain_text(transform: Tag, titulo: str) -> str:
    clone = BeautifulSoup(str(transform), "lxml")
    for tag in clone.select("span.informacao-artigo, img, sup"):
        tag.decompose()
    text = clone.get_text(" ", strip=True)
    if titulo and titulo in text:
        return text
    return text


def _guess_title(citation: str) -> str:
    m = re.search(r"\.\s+([^.]+\S)\s*,\s*v\.\s*", citation)
    return clean_text(m.group(1)) if m else ""


def _parse_autores(
    transform: Tag,
    citation: str,
    titulo: str,
    owner_id: str,
    owner_name: str,
) -> list[dict]:
    autores: list[dict] = []
    links = transform.select("a[href*='lattes.cnpq.br']")
    link_map: dict[str, str] = {}
    for a in links:
        nome = clean_text(a.get_text())
        lid = extract_lattes_id(a.get("href"))
        if nome:
            link_map[nome.upper()] = lid

    author_part = citation
    if titulo and titulo in citation:
        author_part = citation.split(titulo, 1)[0]
    author_part = author_part.strip().rstrip(".")

    chunks = [clean_text(c) for c in author_part.split(";") if clean_text(c)]
    if not chunks:
        for b in transform.select("b"):
            chunks.append(clean_text(b.get_text()))

    for i, chunk in enumerate(chunks, start=1):
        citacao = chunk
        nome_completo = chunk
        if owner_name and owner_name.upper() in chunk.upper():
            nome_completo = owner_name
        autores.append(
            {
                "ordem": str(i),
                "nome_completo": nome_completo,
                "nome_citacao": citacao,
                "lattes_id": link_map.get(chunk.upper(), owner_id if owner_id and owner_name.upper() in chunk.upper() else ""),
            }
        )
    return autores


def _section_name_for_anchor(anchor: Tag) -> str:
    wrapper = anchor.find_parent("div", class_="title-wrapper")
    if not wrapper:
        return ""
    sec = wrapper.find("a", attrs={"name": True})
    return sec.get("name", "") if sec else ""


def _parse_projetos(cv: CurriculumHTML) -> None:
    seen: set[str] = set()
    for anchor in cv.soup.find_all("a", attrs={"name": re.compile(r"^PP_")}):
        if _section_name_for_anchor(anchor) == "ProjetosExtensao":
            continue
        title = anchor.get("name", "")[3:].replace("_", " ").strip()
        if title in seen:
            continue
        seen.add(title)
        date_el = anchor.find_parent("div", class_="data-cell")
        if not date_el:
            continue
        date_b = date_el.select_one("div.layout-cell-3 b")
        period = clean_text(date_b.get_text()) if date_b else ""
        description = ""
        for block in date_el.select("div.layout-cell-9 div.layout-cell-pad-5"):
            chunk = clean_text(block.get_text("\n", strip=True))
            if chunk.lower().startswith("descri"):
                description = re.sub(r"^descri[cç][aã]o:\s*", "", chunk, flags=re.I).strip()
                break
        if not description:
            desc_cell = date_el.select_one("div.layout-cell-9")
            if desc_cell:
                description = clean_text(desc_cell.get_text("\n", strip=True))[:500]
        cv.projetos.append({"titulo": title, "periodo": period, "descricao": description})


def _parse_idiomas(cv: CurriculumHTML) -> None:
    wrapper = _section_after_anchor(cv.soup, "Idiomas")
    if not wrapper:
        return
    for left in wrapper.select("div.layout-cell-3.text-align-right"):
        idioma = clean_text(left.get_text())
        if not idioma or idioma.lower() == "idioma":
            continue
        right = left.find_next_sibling("div", class_="layout-cell-9")
        if not right:
            continue
        cv.idiomas.append(
            {
                "idioma": idioma,
                "prova": clean_text(right.get_text(" ", strip=True)),
            }
        )
