from sqlmodel import Session, select

from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload, PdfSection, Orientacao


def main(session: Session) -> None:
        p = session.exec(
            select(Professor).where(Professor.email == "camilla.tavares@ufma.br")
        ).first()
        u = session.exec(
            select(CurriculoUpload)
            .where(CurriculoUpload.professor_id == p.id)
            .order_by(CurriculoUpload.data_upload.desc())
        ).first()
        ori = session.exec(
            select(Orientacao).where(Orientacao.professor_id == p.id)
        ).all()
        print(f"Total orientacoes professor: {len(ori)}")
        print(f"Upload: {u.arquivo_nome} status={u.status}")
        secs = session.exec(
            select(PdfSection).where(PdfSection.curriculo_upload_id == u.id)
        ).all()
        print(f"Secoes: {len(secs)}")
        for x in secs:
            if "orient" in (x.nome_secao or "").lower():
                print(
                    f"  - {x.nome_secao} | extracao={x.status_extracao} | "
                    f"chars={len(x.texto_secao or '')}"
                )


if __name__ == "__main__":
    with Session(engine) as session:
        main(session)
