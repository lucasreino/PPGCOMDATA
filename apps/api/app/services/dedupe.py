"""Deduplication helpers for extracted curriculum items."""

import re
import unicodedata
from typing import Optional

from sqlmodel import Session, select

from app.models.data import Producao, Projeto, Orientacao, Evento


def normalize_text_key(value: str, max_len: int = 200) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()[:max_len]


def producao_already_exists(
    session: Session,
    professor_id: str,
    curriculo_upload_id: Optional[str],
    titulo: str,
    ano: Optional[int],
    tipo: Optional[str] = None,
) -> bool:
    title_key = normalize_text_key(titulo)
    if not title_key:
        return False

    stmt = select(Producao).where(Producao.professor_id == professor_id)
    if curriculo_upload_id:
        stmt = stmt.where(Producao.curriculo_upload_id == curriculo_upload_id)
    for row in session.exec(stmt).all():
        if normalize_text_key(row.titulo) != title_key:
            continue
        if ano is not None and row.ano is not None and row.ano != ano:
            continue
        if tipo and row.tipo and row.tipo.lower() != tipo.lower():
            continue
        return True
    return False


def projeto_already_exists(
    session: Session,
    professor_id: str,
    curriculo_upload_id: Optional[str],
    titulo: str,
    ano_inicio: Optional[int] = None,
) -> bool:
    title_key = normalize_text_key(titulo)
    if not title_key:
        return False
    stmt = select(Projeto).where(Projeto.professor_id == professor_id)
    if curriculo_upload_id:
        stmt = stmt.where(Projeto.curriculo_upload_id == curriculo_upload_id)
    for row in session.exec(stmt).all():
        if normalize_text_key(row.titulo) == title_key:
            if ano_inicio is None or row.ano_inicio is None or row.ano_inicio == ano_inicio:
                return True
    return False


def orientacao_already_exists(
    session: Session,
    professor_id: str,
    curriculo_upload_id: Optional[str],
    nome_orientando: Optional[str],
    titulo_trabalho: Optional[str],
    ano_inicio: Optional[int] = None,
) -> bool:
    key = normalize_text_key(nome_orientando or titulo_trabalho or "")
    if not key:
        return False
    stmt = select(Orientacao).where(Orientacao.professor_id == professor_id)
    if curriculo_upload_id:
        stmt = stmt.where(Orientacao.curriculo_upload_id == curriculo_upload_id)
    for row in session.exec(stmt).all():
        row_key = normalize_text_key(row.nome_orientando or row.titulo_trabalho or "")
        if row_key == key:
            if ano_inicio is None or row.ano_inicio is None or row.ano_inicio == ano_inicio:
                return True
    return False


def evento_already_exists(
    session: Session,
    professor_id: str,
    curriculo_upload_id: Optional[str],
    nome_evento: str,
    ano: Optional[int] = None,
    eh_organizacao: bool = False,
) -> bool:
    title_key = normalize_text_key(nome_evento)
    if not title_key:
        return False
    stmt = select(Evento).where(
        Evento.professor_id == professor_id,
        Evento.eh_organizacao == eh_organizacao,
    )
    if curriculo_upload_id:
        stmt = stmt.where(Evento.curriculo_upload_id == curriculo_upload_id)
    for row in session.exec(stmt).all():
        if normalize_text_key(row.nome_evento) == title_key:
            if ano is None or row.ano is None or row.ano == ano:
                return True
    return False
