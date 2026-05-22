"""Reprocessa o último upload da Camilla e imprime contagem de orientações."""

from sqlmodel import Session, select

from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload, Orientacao, PdfSection
from app.services.upload_pipeline import run_full_pipeline


def main() -> None:
    with Session(engine) as session:
        prof = session.exec(
            select(Professor).where(Professor.email == "camilla.tavares@ufma.br")
        ).first()
        upload = session.exec(
            select(CurriculoUpload)
            .where(CurriculoUpload.professor_id == prof.id)
            .order_by(CurriculoUpload.data_upload.desc())
        ).first()
        print(f"Reprocessando {upload.arquivo_nome} ({upload.id})")
        result = run_full_pipeline(session, str(upload.id))
        print("Pipeline:", result)
        session.refresh(upload)
        ori = session.exec(
            select(Orientacao).where(Orientacao.professor_id == prof.id)
        ).all()
        print(f"Orientacoes no banco: {len(ori)}")
        secs = session.exec(
            select(PdfSection).where(PdfSection.curriculo_upload_id == upload.id)
        ).all()
        for s in secs:
            if "orient" in (s.nome_secao or "").lower():
                print(f"  {s.nome_secao}: extracao={s.status_extracao}")


if __name__ == "__main__":
    main()
