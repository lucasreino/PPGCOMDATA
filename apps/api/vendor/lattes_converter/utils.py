import re
from html import escape as html_escape
from urllib.parse import parse_qs, urlparse


def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def br_lines_to_list(element) -> list[str]:
    """Extrai linhas de um bloco HTML separadas por <br>."""
    if element is None:
        return []
    parts: list[str] = []
    for child in element.children:
        name = getattr(child, "name", None)
        if name == "br":
            continue
        if name is None:
            chunk = str(child).strip()
            if chunk:
                parts.append(chunk)
        else:
            parts.append(child.get_text(" ", strip=True))
    text = element.get_text("\n", strip=True)
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


def parse_cvuri(cvuri: str | None) -> dict[str, str]:
    if not cvuri:
        return {}
    query = urlparse(cvuri).query
    if not query and "?" in cvuri:
        query = cvuri.split("?", 1)[1]
    parsed = parse_qs(query, keep_blank_values=True)
    return {k: (v[0] if v else "") for k, v in parsed.items()}


def date_br_to_lattes(date_br: str) -> str:
    """13/05/2026 -> 13052026"""
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", date_br.strip())
    if not m:
        return ""
    d, mo, y = m.groups()
    return f"{d}{mo}{y}"


def parse_year_range(label: str) -> tuple[str, str, str]:
    """
    Retorna (inicio, fim, status).
    Ex.: '2012 - 2015' -> ('2012','2015','CONCLUIDO')
         '2006 interrompida' -> ('2006','','INTERROMPIDO')
    """
    label = clean_text(label)
    interrupted = "interromp" in label.lower()
    nums = re.findall(r"\d{4}", label)
    if not nums:
        return "", "", "CONCLUIDO"
    start = nums[0]
    end = nums[1] if len(nums) > 1 and not interrupted else ""
    status = "INTERROMPIDO" if interrupted else "CONCLUIDO"
    return start, end, status


def xml_attr(value: str) -> str:
    if value is None:
        return ""
    return html_escape(str(value), quote=True)


def extract_lattes_id(href: str | None) -> str:
    if not href:
        return ""
    m = re.search(r"lattes\.cnpq\.br/(\d{16})", href)
    return m.group(1) if m else ""


def parse_institution_line(line: str) -> tuple[str, str, str]:
    """
    'Universidade Federal do Maranhão, UFMA, Brasil.' ->
    (nome, sigla, pais)
    """
    line = line.rstrip(".").strip()
    parts = [p.strip() for p in line.split(",")]
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], parts[1], ""
    return line, "", ""


def field_after_label(text: str, label: str) -> str:
    pattern = rf"{re.escape(label)}\s*:?\s*(.+?)(?=(?:\n|Título:|Titulo:|Orientador:|Bolsista|Palavras-chave:|Grande área:|Grande area:|com período|$))"
    m = re.search(pattern, text, re.I | re.S)
    return clean_text(m.group(1)) if m else ""
