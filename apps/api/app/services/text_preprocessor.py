"""Normalização de texto extraído de PDFs Lattes antes do split por seções."""

from __future__ import annotations

import re
import unicodedata

# Rodapés/cabeçalhos repetidos no PDF do Lattes
_NOISE_LINE_PATTERNS = (
    re.compile(r"curr[ií]culo\s+lattes", re.I),
    re.compile(r"lattes\.cnpq\.br", re.I),
    re.compile(r"http[s]?://", re.I),
    re.compile(r"última\s+atualiza", re.I),
    re.compile(r"^\s*página\s+\d+\s+de\s+\d+\s*$", re.I),
    re.compile(r"^\s*page\s+\d+\s+of\s+\d+\s*$", re.I),
)

# Garante que títulos padrão comecem em linha nova (ajuda o regex do section_detector)
_SECTION_HEADER_HINTS = (
    "Dados gerais",
    "Formação acadêmica/titulação",
    "Atuação profissional",
    "Projetos de pesquisa",
    "Projetos de extensão",
    "Produção bibliográfica",
    "Artigos completos publicados em periódicos",
    "Orientações e supervisões",
    "Participação em eventos",
    "Organização de eventos",
    "Produção técnica",
    "Bancas",
    "Prêmios e títulos",
)


def _is_noise_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) < 4:
        return False
    return any(p.search(stripped) for p in _NOISE_LINE_PATTERNS)


def normalize_lattes_text(text: str) -> str:
    """Limpa e padroniza texto bruto do PyMuPDF para melhor detecção de seções."""
    if not text:
        return ""

    text = text.replace("\x00", "")
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Hifenização de quebra de linha: "comunica-\nção" -> "comunicação"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    lines: list[str] = []
    for line in text.split("\n"):
        if _is_noise_line(line):
            continue
        line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    for header in _SECTION_HEADER_HINTS:
        text = re.sub(
            rf"(?<!\n)({re.escape(header)})",
            r"\n\1",
            text,
            flags=re.IGNORECASE,
        )

    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
