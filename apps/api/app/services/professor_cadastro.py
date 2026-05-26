"""Cadastro de docente com foto e importação de currículo XML Lattes."""

from __future__ import annotations

import os
import re
import shutil
from typing import Any, Optional

from fastapi import UploadFile
from sqlmodel import Session

from app.config import settings
from app.models.core import Professor
from app.models.enums import TipoDocente
from app.services.lattes_curriculo_import import save_and_import_lattes_file
from app.services.professor_foto import FOTO_EXTENSIONS, fotos_dir, slug_for_nome
from app.services.professor_lookup import find_professor, normalize_lattes_id
from app.services.professor_oficial import register_official_professor

FOTO_MIME = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def parse_lattes_id(link: Optional[str], explicit: Optional[str]) -> Optional[str]:
    if explicit and explicit.strip():
        return normalize_lattes_id(explicit.strip())
    if not link or not link.strip():
        return None
    match = re.search(r"lattes\.cnpq\.br/(\d+)", link.strip(), re.I)
    if match:
        return match.group(1)
    return normalize_lattes_id(link.strip())


def build_observacoes(grupo_pesquisa: Optional[str], tematicas: Optional[str]) -> Optional[str]:
    parts: list[str] = []
    if grupo_pesquisa and grupo_pesquisa.strip():
        parts.append(f"Grupo de pesquisa: {grupo_pesquisa.strip()}")
    if tematicas and tematicas.strip():
        parts.append(f"Temáticas: {tematicas.strip()}")
    return "\n".join(parts) if parts else None


def save_professor_photo(
    prof: Professor,
    file: UploadFile,
    *,
    api_prefix: str = "/api/v1/fotos",
) -> str:
    """Salva imagem em data/fotos e retorna foto_url."""
    ext = ""
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
    if ext not in FOTO_EXTENSIONS:
        mime_ext = FOTO_MIME.get((file.content_type or "").lower(), "")
        ext = mime_ext or ".jpg"
    if ext not in FOTO_EXTENSIONS:
        raise ValueError("Formato de imagem não suportado. Use JPG, PNG, WEBP ou GIF.")

    slug = slug_for_nome(prof.nome_completo) or str(prof.id)
    base = fotos_dir()
    base.mkdir(parents=True, exist_ok=True)

    dest = base / f"{slug}{ext}"
    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)

    return f"{api_prefix}/{dest.name}"


def import_xml_curriculo(
    session: Session,
    prof: Professor,
    file: UploadFile,
) -> dict[str, Any]:
    """Importa XML Lattes no cadastro de docente."""
    return save_and_import_lattes_file(
        session,
        str(prof.id),
        file,
        "xml",
    )


def cadastrar_professor(
    session: Session,
    *,
    nome_completo: str,
    email: Optional[str] = None,
    link_lattes: Optional[str] = None,
    id_lattes: Optional[str] = None,
    tipo_docente: TipoDocente = TipoDocente.PERMANENTE,
    linha_pesquisa_id: Optional[str] = None,
    grupo_pesquisa: Optional[str] = None,
    tematicas: Optional[str] = None,
    xml_file: Optional[UploadFile] = None,
    foto_file: Optional[UploadFile] = None,
) -> dict[str, Any]:
    """Cria docente e processa foto/XML opcionais."""
    nome = (nome_completo or "").strip()
    if not nome:
        raise ValueError("Nome completo é obrigatório.")

    lid = parse_lattes_id(link_lattes, id_lattes)
    existing = find_professor(
        session,
        nome_completo=nome,
        email=email,
        id_lattes=lid,
    )
    if existing:
        raise ValueError(f"Docente já cadastrado: {existing.nome_completo}")

    prof = Professor(
        nome_completo=nome,
        email=(email or "").strip() or None,
        link_lattes=(link_lattes or "").strip() or None,
        id_lattes=lid,
        tipo_docente=tipo_docente,
        linha_pesquisa_id=linha_pesquisa_id or None,
        observacoes=build_observacoes(grupo_pesquisa, tematicas),
        status=True,
    )
    session.add(prof)
    session.commit()
    session.refresh(prof)

    official_entry = register_official_professor(
        session,
        nome_completo=nome,
        email=prof.email,
        link_lattes=prof.link_lattes,
        id_lattes=prof.id_lattes,
        tipo_docente=tipo_docente,
        linha_pesquisa_id=linha_pesquisa_id,
        grupo_pesquisa=grupo_pesquisa,
        tematicas=tematicas,
    )

    result: dict[str, Any] = {
        "professor_id": str(prof.id),
        "nome_completo": prof.nome_completo,
        "cadastro_oficial": True,
        "linha_oficial": official_entry.get("linha"),
        "xml_importado": False,
        "foto_url": None,
        "upload_id": None,
    }

    if foto_file and foto_file.filename:
        prof.foto_url = save_professor_photo(prof, foto_file)
        session.add(prof)
        session.commit()
        session.refresh(prof)
        result["foto_url"] = prof.foto_url

    if xml_file and xml_file.filename:
        xml_result = import_xml_curriculo(session, prof, xml_file)
        session.refresh(prof)
        result.update(xml_result)
        result["id_lattes"] = prof.id_lattes
        register_official_professor(
            session,
            nome_completo=prof.nome_completo,
            email=prof.email,
            link_lattes=prof.link_lattes,
            id_lattes=prof.id_lattes,
            tipo_docente=prof.tipo_docente,
            linha_pesquisa_id=linha_pesquisa_id,
            grupo_pesquisa=grupo_pesquisa,
            tematicas=tematicas,
        )

    return result
