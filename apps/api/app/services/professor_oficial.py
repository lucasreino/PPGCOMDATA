"""Cadastro oficial de docentes: lista base + inclusões via painel admin."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from sqlmodel import Session

from app.models.core import LinhaPesquisa
from app.models.enums import TipoDocente
from app.services.professor_lookup import normalize_lattes_id, normalize_text

LINE1_NAME = "Tecnologias, Audiovisual e Processos Regionais de Comunicação"
LINE2_NAME = "Processos Comunicacionais, Cidadania e Identidades"

_CADASTRO_DIR = Path(__file__).resolve().parent.parent / "cadastro_oficial"
ADDITIONS_FILE = _CADASTRO_DIR / "professores_adicionados.json"


def _ensure_cadastro_dir() -> None:
    _CADASTRO_DIR.mkdir(parents=True, exist_ok=True)


def load_additions_raw() -> list[dict[str, Any]]:
    """Entradas adicionadas pelo painel (JSON serializável)."""
    if not ADDITIONS_FILE.is_file():
        return []
    try:
        data = json.loads(ADDITIONS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def save_additions_raw(entries: list[dict[str, Any]]) -> None:
    _ensure_cadastro_dir()
    ADDITIONS_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _entry_key(entry: dict[str, Any]) -> str:
    email = normalize_text(entry.get("email"))
    if email:
        return f"email:{email}"
    lid = normalize_lattes_id(entry.get("id_lattes"))
    if lid:
        return f"lattes:{lid}"
    return f"nome:{normalize_text(entry.get('nome_completo'))}"


def _to_tipo_docente(value: Any) -> TipoDocente:
    if isinstance(value, TipoDocente):
        return value
    raw = str(value or "permanente").strip().lower()
    try:
        return TipoDocente(raw)
    except ValueError:
        return TipoDocente.PERMANENTE


def _hydrate_entry(raw: dict[str, Any]) -> dict[str, Any]:
    """Converte registro JSON para o formato usado pelo seed (com enum)."""
    link = (raw.get("link_lattes") or "").strip()
    lid = normalize_lattes_id(raw.get("id_lattes")) or None
    if not lid and link:
        match = re.search(r"lattes\.cnpq\.br/(\d+)", link, re.I)
        if match:
            lid = match.group(1)
    if lid and not link:
        link = f"http://lattes.cnpq.br/{lid}"

    return {
        "nome_completo": (raw.get("nome_completo") or "").strip(),
        "email": (raw.get("email") or "").strip(),
        "link_lattes": link or None,
        "id_lattes": lid,
        "linha": raw.get("linha") if raw.get("linha") in ("linha1", "linha2") else "linha1",
        "tipo_docente": _to_tipo_docente(raw.get("tipo_docente")),
        "grupo_pesquisa": (raw.get("grupo_pesquisa") or "").strip(),
        "tematicas": (raw.get("tematicas") or "").strip(),
    }


def linha_key_for_professor(
    session: Session,
    linha_pesquisa_id: Optional[str],
) -> str:
    """Mapeia UUID da linha para linha1 / linha2."""
    if not linha_pesquisa_id:
        return "linha1"
    linha = session.get(LinhaPesquisa, linha_pesquisa_id)
    if not linha or not linha.nome:
        return "linha1"
    nome = linha.nome.strip()
    if nome == LINE2_NAME:
        return "linha2"
    if nome == LINE1_NAME:
        return "linha1"
    if "Cidadania" in nome or "Identidades" in nome:
        return "linha2"
    return "linha1"


def get_official_professor_data() -> list[dict[str, Any]]:
    """Lista base (utils_fix_linhas) + docentes incluídos pelo admin."""
    from app.utils_fix_linhas import PROFESSOR_DATA as base

    merged: list[dict[str, Any]] = [dict(d) for d in base]
    keys = {_entry_key(e) for e in merged if _entry_key(e)}

    for raw in load_additions_raw():
        entry = _hydrate_entry(raw)
        if not entry["nome_completo"]:
            continue
        key = _entry_key(entry)
        if key in keys:
            merged = [e for e in merged if _entry_key(e) != key]
        else:
            keys.add(key)
        merged.append(entry)

    return merged


def register_official_professor(
    session: Session,
    *,
    nome_completo: str,
    email: Optional[str],
    link_lattes: Optional[str],
    id_lattes: Optional[str],
    tipo_docente: TipoDocente,
    linha_pesquisa_id: Optional[str],
    grupo_pesquisa: Optional[str],
    tematicas: Optional[str],
) -> dict[str, Any]:
    """Persiste docente no arquivo de cadastro oficial adicional."""
    entry = {
        "nome_completo": nome_completo.strip(),
        "email": (email or "").strip(),
        "link_lattes": (link_lattes or "").strip(),
        "id_lattes": normalize_lattes_id(id_lattes) or id_lattes,
        "linha": linha_key_for_professor(session, linha_pesquisa_id),
        "tipo_docente": tipo_docente.value,
        "grupo_pesquisa": (grupo_pesquisa or "").strip(),
        "tematicas": (tematicas or "").strip(),
    }

    additions = load_additions_raw()
    key = _entry_key(entry)
    updated = False
    for i, raw in enumerate(additions):
        if _entry_key(_hydrate_entry(raw)) == key:
            additions[i] = entry
            updated = True
            break
    if not updated:
        additions.append(entry)

    save_additions_raw(additions)
    return entry


def filename_rules_from_official_data() -> list[tuple[str, str]]:
    """Regras extras para associar PDFs pelo nome do arquivo."""
    rules: list[tuple[str, str]] = []
    seen: set[str] = set()
    for data in get_official_professor_data():
        email = (data.get("email") or "").strip().lower()
        if not email or email in seen:
            continue
        seen.add(email)
        local = email.split("@")[0]
        for needle in re.split(r"[._\-]+", local):
            needle = needle.strip().lower()
            if len(needle) >= 3:
                rules.append((needle, email))
        nome_parts = (data.get("nome_completo") or "").split()
        first = normalize_text(nome_parts[0]) if nome_parts else ""
        if len(first) >= 3:
            rules.append((first, email))
    return rules
