"""Cadastro de docente com foto e importação de currículo XML Lattes."""

from __future__ import annotations

import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import UploadFile
from sqlmodel import Session

from app.config import settings
from app.models.core import Professor
from app.models.data import CurriculoUpload
from app.models.enums import StatusProcessamento, TipoDocente
from app.services.lattes_xml_importer import (
    import_lattes_xml,
    mark_xml_covered_sections_extracted,
)
from app.services.professor_foto import FOTO_EXTENSIONS, fotos_dir, slug_for_nome
from app.services.professor_lookup import find_professor, normalize_lattes_id
from app.services.professor_oficial import register_official_professor
from app.services.upload_cleanup import mark_all_sections_extracted
from app.services.upload_status import refresh_upload_validation_status

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


def _persist_xml_copy(
    prof: Professor,
    xml_path: Path,
) -> None:
    """Copia XML para LATTES_XML_DIR ({id_lattes}.xml) quando configurado."""
    lid = normalize_lattes_id(prof.id_lattes)
    xml_dir = (settings.LATTES_XML_DIR or "").strip()
    if not lid or not xml_dir:
        return
    target_dir = Path(xml_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{lid}.xml"
    shutil.copy2(xml_path, target)


def import_xml_curriculo(
    session: Session,
    prof: Professor,
    file: UploadFile,
) -> dict[str, Any]:
    """Cria registro de upload, importa XML e atualiza status."""
    if not file.filename or not file.filename.lower().endswith(".xml"):
        raise ValueError("O currículo deve ser um arquivo XML exportado do Lattes (.xml).")

    xml_subdir = os.path.join(settings.UPLOAD_DIR, "xml")
    os.makedirs(xml_subdir, exist_ok=True)
    stored_name = f"{uuid.uuid4()}.xml"
    dest_path = os.path.join(xml_subdir, stored_name)

    try:
        with open(dest_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
    except OSError as exc:
        raise ValueError(f"Erro ao salvar XML: {exc}") from exc

    upload = CurriculoUpload(
        professor_id=str(prof.id),
        arquivo_url=dest_path,
        arquivo_nome=file.filename or stored_name,
        status=StatusProcessamento.PROCESSANDO,
    )
    session.add(upload)
    session.commit()
    session.refresh(upload)

    try:
        metrics = import_lattes_xml(session, str(upload.id), dest_path)
        _persist_xml_copy(prof, Path(dest_path))
        mark_xml_covered_sections_extracted(session, str(upload.id))
        mark_all_sections_extracted(session, str(upload.id))
        upload.status = StatusProcessamento.PROCESSADO_COM_SUCESSO
        session.add(upload)
        session.commit()
        refresh_upload_validation_status(session, str(upload.id))
        session.refresh(upload)
        return {
            "upload_id": str(upload.id),
            "xml_importado": True,
            "metrics": metrics,
            "upload_status": upload.status.value,
        }
    except Exception as exc:
        upload.status = StatusProcessamento.ERRO_NO_PROCESSAMENTO
        upload.mensagem_erro = str(exc)
        session.add(upload)
        session.commit()
        raise ValueError(f"Falha ao importar XML Lattes: {exc}") from exc


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
