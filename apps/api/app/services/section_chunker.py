"""Divide seções Lattes muito grandes em blocos menores para a IA."""

from __future__ import annotations

import re
from typing import List

from app.config import settings

# Seções que costumam ter listas longas numeradas
_CHUNKABLE_KEYWORDS = (
    "artigos completos",
    "livros publicados",
    "capítulos de livros",
    "trabalhos completos publicados",
    "orientações e supervisões",
    "orientacoes e supervisoes",
    "participação em eventos",
    "participacao em eventos",
    "organização de eventos",
    "organizacao de eventos",
    "produção técnica",
    "producao tecnica",
    "projetos de pesquisa",
    "projetos de extensão",
    "projetos de extensao",
    "bancas",
)

_NUMBERED_ITEM_RE = re.compile(r"(?:^|\n)(\d+)\.\s", re.MULTILINE)


def _is_chunkable_section(section_name: str) -> bool:
    name = (section_name or "").lower()
    return any(k in name for k in _CHUNKABLE_KEYWORDS)


def _split_numbered_items(text: str) -> List[str]:
    matches = list(_NUMBERED_ITEM_RE.finditer(text))
    if len(matches) < 2:
        return [text]

    items: List[str] = []
    prefix = text[: matches[0].start()].strip()
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        item = text[start:end].strip()
        if item:
            items.append(item)

    if prefix and items:
        items[0] = f"{prefix}\n\n{items[0]}"
    return items or [text]


def _split_by_size(text: str, max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            break_at = text.rfind("\n\n", start, end)
            if break_at > start + max_chars // 2:
                end = break_at
        chunks.append(text[start:end].strip())
        start = end
    return [c for c in chunks if c]


def chunk_section_text(
    section_name: str,
    text: str,
    *,
    max_chars: int | None = None,
    max_items: int | None = None,
) -> List[str]:
    """
    Retorna 1+ blocos de texto para enviar à IA.
    Seções pequenas ou não listáveis retornam lista com o texto original.
    """
    text = (text or "").strip()
    if not text:
        return [""]

    max_chars = max_chars or settings.SECTION_CHUNK_MAX_CHARS
    max_items = max_items or settings.SECTION_CHUNK_MAX_ITEMS

    if len(text) <= max_chars or not _is_chunkable_section(section_name):
        return [text]

    items = _split_numbered_items(text)
    if len(items) <= 1:
        return _split_by_size(text, max_chars)

    chunks: List[str] = []
    buffer = ""
    item_count = 0

    for item in items:
        item = item.strip()
        if not item:
            continue
        would_exceed = buffer and (
            len(buffer) + len(item) + 2 > max_chars or item_count >= max_items
        )
        if would_exceed:
            chunks.append(buffer.strip())
            buffer = item
            item_count = 1
        else:
            buffer = f"{buffer}\n\n{item}".strip() if buffer else item
            item_count += 1

    if buffer.strip():
        chunks.append(buffer.strip())

    return chunks if chunks else [text]
