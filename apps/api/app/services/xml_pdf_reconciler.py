"""Reconcilia extrações PDF/IA com dados XML Lattes (XML tem prioridade)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional, Type

from sqlalchemy import and_
from sqlmodel import Session, SQLModel, select

from app.models.data import (
    AlertaLacuna,
    Banca,
    CurriculoUpload,
    Evento,
    FormacaoAcademica,
    Orientacao,
    PerfilLattes,
    Producao,
    Projeto,
)
from app.models.enums import FonteDado, GravidadeLacuna, StatusValidacao
from app.services.dedupe import normalize_text_key
from app.services.lattes_xml_importer import resolve_xml_path_for_upload

logger = logging.getLogger("ppgcomdata.xml_pdf_reconciler")

_XML = FonteDado.XML_LATTES
_PDF = FonteDado.PDF_LATTES

_OBS_XML_OK = "[reconciliação] Confirmado automaticamente (fonte XML Lattes)."
_OBS_PDF_DROP = "[reconciliação] Descartado: duplicata do PDF; prevalece o XML."
_LACUNA_TIPO = "ausencia_xml"


@dataclass
class ReconcileEntityStats:
    entidade: str
    xml_confirmados: int = 0
    pdf_descartados: int = 0
    pdf_so_pdf_pendentes: int = 0
    pares_encontrados: int = 0
    lacunas_criadas: int = 0


@dataclass
class ReconcileUploadResult:
    upload_id: str
    reconciliado: bool = False
    motivo_skip: Optional[str] = None
    entidades: list[ReconcileEntityStats] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reconciliado": self.reconciliado,
            "motivo_skip": self.motivo_skip,
            "totais": {
                "xml_confirmados": sum(e.xml_confirmados for e in self.entidades),
                "pdf_descartados": sum(e.pdf_descartados for e in self.entidades),
                "pdf_so_pdf_pendentes": sum(e.pdf_so_pdf_pendentes for e in self.entidades),
                "pares_encontrados": sum(e.pares_encontrados for e in self.entidades),
                "lacunas_criadas": sum(e.lacunas_criadas for e in self.entidades),
            },
            "entidades": [e.__dict__ for e in self.entidades],
        }


def _years_equal(a: Optional[int], b: Optional[int]) -> bool:
    if a is None or b is None:
        return True
    return a == b


def _texts_similar(a: Optional[str], b: Optional[str]) -> bool:
    ka = normalize_text_key(a or "")
    kb = normalize_text_key(b or "")
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    if len(ka) >= 12 and len(kb) >= 12:
        return ka in kb or kb in ka
    return False


def _any_text_match(
    left: Iterable[Optional[str]],
    right: Iterable[Optional[str]],
) -> bool:
    for a in left:
        if not a:
            continue
        for b in right:
            if _texts_similar(a, b):
                return True
    return False


def _eligible_for_auto(row: Any) -> bool:
    status = getattr(row, "status_validacao", None)
    return status in (StatusValidacao.PENDENTE, StatusValidacao.INCOMPLETO)


def _append_obs(row: Any, note: str) -> None:
    if not hasattr(row, "observacoes"):
        return
    prev = getattr(row, "observacoes", None) or ""
    if note in prev:
        return
    row.observacoes = f"{prev}\n{note}".strip() if prev else note


def _confirm_row(row: Any) -> None:
    if not _eligible_for_auto(row):
        return
    row.status_validacao = StatusValidacao.CONFIRMADO
    _append_obs(row, _OBS_XML_OK)


def _discard_row(row: Any) -> None:
    if not _eligible_for_auto(row):
        return
    row.status_validacao = StatusValidacao.DESCARTADO
    _append_obs(row, _OBS_PDF_DROP)


def _load_split(
    session: Session,
    model: Type[SQLModel],
    upload_id: str,
) -> tuple[list[Any], list[Any]]:
    col = model.__table__.c.get("curriculo_upload_id")  # type: ignore[union-attr]
    if col is None:
        return [], []
    stmt = select(model).where(col == str(upload_id))
    rows = list(session.exec(stmt).all())
    pdf_rows = [r for r in rows if getattr(r, "fonte_dado", None) == _PDF]
    xml_rows = [r for r in rows if getattr(r, "fonte_dado", None) == _XML]
    return pdf_rows, xml_rows


def _reconcile_lists(
    session: Session,
    upload: CurriculoUpload,
    entity_label: str,
    pdf_rows: list[Any],
    xml_rows: list[Any],
    match_fn: Callable[[Any, Any], bool],
    pdf_label_fn: Callable[[Any], str],
) -> ReconcileEntityStats:
    stats = ReconcileEntityStats(entidade=entity_label)
    used_xml_ids: set[str] = set()

    for pdf in pdf_rows:
        partner = None
        for xml in xml_rows:
            if xml.id in used_xml_ids:
                continue
            if match_fn(pdf, xml):
                partner = xml
                break
        if partner:
            used_xml_ids.add(partner.id)
            stats.pares_encontrados += 1
            if _eligible_for_auto(partner):
                _confirm_row(partner)
                stats.xml_confirmados += 1
                session.add(partner)
            if _eligible_for_auto(pdf):
                _discard_row(pdf)
                stats.pdf_descartados += 1
                session.add(pdf)
            _resolve_pdf_lacuna(session, upload, str(pdf.id))
        elif _eligible_for_auto(pdf):
            stats.pdf_so_pdf_pendentes += 1
            if _create_pdf_only_lacuna(session, upload, entity_label, pdf, pdf_label_fn(pdf)):
                stats.lacunas_criadas += 1

    for xml in xml_rows:
        if xml.id in used_xml_ids:
            continue
        if _eligible_for_auto(xml):
            _confirm_row(xml)
            stats.xml_confirmados += 1
            session.add(xml)

    return stats


def _resolve_pdf_lacuna(session: Session, upload: CurriculoUpload, entidade_id: str) -> None:
    rows = session.exec(
        select(AlertaLacuna).where(
            and_(
                AlertaLacuna.curriculo_upload_id == str(upload.id),
                AlertaLacuna.entidade_id == str(entidade_id),
                AlertaLacuna.tipo_lacuna == _LACUNA_TIPO,
                AlertaLacuna.resolvido == False,  # noqa: E712
            )
        )
    ).all()
    for lac in rows:
        lac.resolvido = True
        session.add(lac)


def _create_pdf_only_lacuna(
    session: Session,
    upload: CurriculoUpload,
    entity_label: str,
    pdf_row: Any,
    label: str,
) -> bool:
    existing = session.exec(
        select(AlertaLacuna).where(
            and_(
                AlertaLacuna.curriculo_upload_id == str(upload.id),
                AlertaLacuna.entidade_id == str(pdf_row.id),
                AlertaLacuna.tipo_lacuna == _LACUNA_TIPO,
                AlertaLacuna.resolvido == False,  # noqa: E712
            )
        )
    ).first()
    if existing:
        return False
    session.add(
        AlertaLacuna(
            professor_id=str(upload.professor_id),
            curriculo_upload_id=str(upload.id),
            tipo_lacuna=_LACUNA_TIPO,
            descricao=(
                f"Item extraído do PDF sem par correspondente no XML: {label}"
            )[:500],
            gravidade=GravidadeLacuna.MEDIA,
            acao_recomendada="Revisar manualmente ou confirmar se o XML está incompleto.",
            resolvido=False,
            entidade_relacionada=entity_label,
            entidade_id=str(pdf_row.id),
        )
    )
    return True


# --- matchers ---


def _match_producao(pdf: Producao, xml: Producao) -> bool:
    if pdf.tipo and xml.tipo and pdf.tipo.lower() != xml.tipo.lower():
        return False
    if not _years_equal(pdf.ano, xml.ano):
        return False
    return _texts_similar(pdf.titulo, xml.titulo)


def _match_projeto(pdf: Projeto, xml: Projeto) -> bool:
    if not _years_equal(pdf.ano_inicio, xml.ano_inicio):
        return False
    return _texts_similar(pdf.titulo, xml.titulo)


def _match_orientacao(pdf: Orientacao, xml: Orientacao) -> bool:
    pdf_texts = [pdf.nome_orientando, pdf.titulo_trabalho]
    xml_texts = [xml.nome_orientando, xml.titulo_trabalho]
    if not _any_text_match(pdf_texts, xml_texts):
        return False
    return _years_equal(
        pdf.ano_conclusao or pdf.ano_inicio,
        xml.ano_conclusao or xml.ano_inicio,
    )


def _match_banca(pdf: Banca, xml: Banca) -> bool:
    if not _years_equal(pdf.ano, xml.ano):
        return False
    return _any_text_match(
        [pdf.nome_candidato, pdf.titulo_trabalho],
        [xml.nome_candidato, xml.titulo_trabalho],
    )


def _match_evento(pdf: Evento, xml: Evento) -> bool:
    if pdf.eh_organizacao != xml.eh_organizacao:
        return False
    if not _years_equal(pdf.ano, xml.ano):
        return False
    return _texts_similar(pdf.nome_evento, xml.nome_evento)


def _match_formacao(pdf: FormacaoAcademica, xml: FormacaoAcademica) -> bool:
    if pdf.nivel != xml.nivel:
        return False
    if not _years_equal(pdf.ano_fim, xml.ano_fim):
        return False
    return _texts_similar(pdf.curso, xml.curso) or _texts_similar(
        pdf.instituicao, xml.instituicao
    )


def _match_perfil(pdf: PerfilLattes, xml: PerfilLattes) -> bool:
    return True


_ENTITY_SPECS: list[
    tuple[
        str,
        Type[SQLModel],
        Callable[[Any, Any], bool],
        Callable[[Any], str],
    ]
] = [
    ("producoes", Producao, _match_producao, lambda r: r.titulo or ""),
    ("projetos", Projeto, _match_projeto, lambda r: r.titulo or ""),
    ("orientacoes", Orientacao, _match_orientacao, lambda r: r.nome_orientando or r.titulo_trabalho or ""),
    ("bancas", Banca, _match_banca, lambda r: r.nome_candidato or r.titulo_trabalho or ""),
    ("eventos", Evento, _match_evento, lambda r: r.nome_evento or ""),
    ("formacoes_academicas", FormacaoAcademica, _match_formacao, lambda r: r.curso or r.instituicao or ""),
    ("perfis_lattes", PerfilLattes, _match_perfil, lambda r: "perfil"),
]


def reconcile_upload_xml_pdf(
    session: Session,
    upload_id: str,
    *,
    xml_dir: Optional[str] = None,
) -> ReconcileUploadResult:
    """
    Após importação XML + extração PDF/IA:
    - confirma registros XML (fonte primária);
    - descarta duplicatas PDF/IA correspondentes;
    - mantém PDF-only como pendente + lacuna.
    """
    result = ReconcileUploadResult(upload_id=upload_id)
    upload = session.get(CurriculoUpload, upload_id)
    if not upload:
        result.motivo_skip = "upload_nao_encontrado"
        return result

    if not resolve_xml_path_for_upload(session, upload_id, xml_dir=xml_dir):
        result.motivo_skip = "xml_nao_disponivel"
        return result

    has_xml = False
    for label, model, match_fn, label_fn in _ENTITY_SPECS:
        pdf_rows, xml_rows = _load_split(session, model, upload_id)
        if xml_rows:
            has_xml = True
        if not pdf_rows and not xml_rows:
            continue
        stats = _reconcile_lists(
            session,
            upload,
            label,
            pdf_rows,
            xml_rows,
            match_fn,
            label_fn,
        )
        result.entidades.append(stats)
        if stats.pares_encontrados or stats.xml_confirmados or stats.pdf_descartados:
            logger.info(
                "Reconciliação %s upload=%s: %s",
                label,
                upload_id,
                stats,
            )

    if not has_xml:
        result.motivo_skip = "sem_registros_xml"
        return result

    session.commit()
    result.reconciliado = True
    return result
