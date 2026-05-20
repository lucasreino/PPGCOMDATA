from sqlmodel import Session, select

from app.models.data import CurriculoUpload, Projeto, Evento, Producao, Financiamento
from app.models.enums import StatusProcessamento, StatusValidacao

PENDING_MODELS = (Projeto, Evento, Producao, Financiamento)


def count_pending_for_upload(session: Session, upload_id: str) -> int:
    total = 0
    for model in PENDING_MODELS:
        if not hasattr(model, "curriculo_upload_id"):
            continue
        stmt = (
            select(model)
            .where(model.curriculo_upload_id == upload_id)
            .where(model.status_validacao == StatusValidacao.PENDENTE)
        )
        total += len(session.exec(stmt).all())
    return total


def refresh_upload_validation_status(session: Session, upload_id: str) -> CurriculoUpload | None:
    """Atualiza o status do upload conforme itens pendentes de validação humana."""
    upload = session.get(CurriculoUpload, upload_id)
    if not upload:
        return None

    if upload.status in (
        StatusProcessamento.AGUARDANDO_PROCESSAMENTO,
        StatusProcessamento.PROCESSANDO,
        StatusProcessamento.ERRO_NO_PROCESSAMENTO,
    ):
        return upload

    pending = count_pending_for_upload(session, upload_id)
    if pending == 0:
        upload.status = StatusProcessamento.VALIDADO
    else:
        upload.status = StatusProcessamento.AGUARDANDO_VALIDACAO

    session.add(upload)
    session.commit()
    session.refresh(upload)
    return upload
