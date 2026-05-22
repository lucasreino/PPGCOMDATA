"""Marca todos os registros xml_lattes como confirmados."""

from sqlmodel import Session, select

from app.database import engine
from app.models.data import (
    Banca,
    CurriculoUpload,
    Evento,
    FormacaoAcademica,
    Orientacao,
    PerfilLattes,
    Producao,
    Projeto,
)
from app.models.enums import FonteDado, StatusValidacao
from app.services.upload_status import refresh_upload_validation_status

MODELS = (Producao, Projeto, Orientacao, Banca, Evento, FormacaoAcademica, PerfilLattes)


def main() -> None:
    with Session(engine) as session:
        count = 0
        for model in MODELS:
            rows = session.exec(
                select(model).where(
                    model.fonte_dado == FonteDado.XML_LATTES,
                    model.status_validacao == StatusValidacao.PENDENTE,
                )
            ).all()
            for row in rows:
                row.status_validacao = StatusValidacao.CONFIRMADO
                session.add(row)
                count += 1
        session.commit()
        uploads = session.exec(select(CurriculoUpload)).all()
        for upload in uploads:
            refresh_upload_validation_status(session, str(upload.id))
        print(f"Registros XML confirmados: {count}")
        print(f"Uploads atualizados: {len(uploads)}")


if __name__ == "__main__":
    main()
