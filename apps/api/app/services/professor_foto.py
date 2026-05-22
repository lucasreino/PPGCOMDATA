"""Resolve fotos em data/fotos (slug por nome do arquivo)."""

from __future__ import annotations

import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Optional

# Slug do arquivo (sem extensão) por nome completo — chaves normalizadas (sem acento)
NOME_PARA_SLUG_RAW: dict[str, str] = {
    "Izani Pibernat Mustafá": "izani",
    "José Carlos Messias Santos Franco": "jose-messias",
    "Larissa Leda Fonseca Rocha": "larissa",
    "Marcelli Alves da Silva": "marcelli",
    "Domingos Alves de Almeida": "domingos",
    "Odlinari Ramon Nascimento da Silva": "odlinari",
    "Camilla Quesada Tavares": "camilla",
    "Leila Lima de Sousa": "leila",
    "Letícia Conceição Martins Cardoso": "leticia",
    "Thaisa Cristina Bueno": "thaisa",
    "Maria Gislene Carvalho Fonseca": "maria-gislene",
    "Thays Assunção Reis": "thays",
    "Michelly Santos de Carvalho": "michelly",
}

FOTO_EXTENSIONS = (".gif", ".jpg", ".jpeg", ".png", ".webp")


def _normalize_name(name: str) -> str:
    n = unicodedata.normalize("NFD", name.strip().lower())
    return "".join(c for c in n if unicodedata.category(c) != "Mn")


NOME_PARA_SLUG: dict[str, str] = {
    _normalize_name(k): v for k, v in NOME_PARA_SLUG_RAW.items()
}


def fotos_dir() -> Path:
    here = Path(__file__).resolve()
    repo_data = here.parents[4] / "data" / "fotos" if len(here.parents) > 4 else None
    workspace_data = here.parents[2] / "data" / "fotos" if len(here.parents) > 2 else None

    candidates = [
        os.environ.get("FOTOS_DIR"),
        "/workspace/data/fotos",
        workspace_data,
        repo_data,
        Path.cwd() / "data" / "fotos",
    ]
    for c in candidates:
        if not c:
            continue
        p = Path(c)
        if p.is_dir():
            return p
    return Path("/workspace/data/fotos")


@lru_cache(maxsize=1)
def _index_fotos() -> dict[str, str]:
    """slug -> nome do arquivo (ex.: camilla.gif)."""
    index: dict[str, str] = {}
    base = fotos_dir()
    if not base.is_dir():
        return index
    for path in base.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() not in FOTO_EXTENSIONS:
            continue
        index[path.stem.lower()] = path.name
    return index


def slug_for_nome(nome_completo: str) -> Optional[str]:
    key = _normalize_name(nome_completo)
    if key in NOME_PARA_SLUG:
        return NOME_PARA_SLUG[key]
    parts = re.sub(r"[^a-z0-9\s-]", "", key).split()
    if not parts:
        return None
    if len(parts) >= 2 and parts[0] in ("jose", "maria", "joao"):
        return f"{parts[0]}-{parts[1]}"
    return parts[0]


def resolve_foto_filename(
    nome_completo: str,
    id_lattes: Optional[str] = None,
    professor_id: Optional[str] = None,
) -> Optional[str]:
    """Retorna o nome do arquivo de foto, se existir em data/fotos."""
    index = _index_fotos()
    if not index:
        return None

    slug = slug_for_nome(nome_completo or "")
    if slug and slug in index:
        return index[slug]

    if id_lattes and id_lattes in index:
        return index[id_lattes]

    if professor_id and professor_id in index:
        return index[professor_id]

    return None


def resolve_foto_url(
    nome_completo: str,
    id_lattes: Optional[str] = None,
    professor_id: Optional[str] = None,
    *,
    api_prefix: str = "/api/v1/fotos",
) -> Optional[str]:
    filename = resolve_foto_filename(nome_completo, id_lattes, professor_id)
    if not filename:
        return None
    return f"{api_prefix}/{filename}"
