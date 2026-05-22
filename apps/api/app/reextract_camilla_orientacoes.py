"""Reextrai só as seções de orientação da Camilla (concluídas falhou com JSON list)."""

from sqlmodel import Session, select

from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload, Orientacao, PdfSection
from app.services.ai_extractor import extract_and_save_section_data


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
        secs = session.exec(
            select(PdfSection)
            .where(PdfSection.curriculo_upload_id == upload.id)
            .where(PdfSection.nome_secao.ilike("%orient%"))
        ).all()
        before = len(
            session.exec(select(Orientacao).where(Orientacao.professor_id == prof.id)).all()
        )
        print(f"Orientacoes antes: {before}")
        for sec in secs:
            if sec.status_extracao:
                print(f"Pulando (ja ok): {sec.nome_secao}")
                continue
            print(f"Extraindo: {sec.nome_secao} ({sec.id})")
            sec.status_extracao = False
            session.add(sec)
            session.commit()
            metrics = extract_and_save_section_data(session, str(sec.id))
            print(f"  -> {metrics}")
        after = len(
            session.exec(select(Orientacao).where(Orientacao.professor_id == prof.id)).all()
        )
        print(f"Orientacoes depois: {after}")


if __name__ == "__main__":
    main()
