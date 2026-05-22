"""Resumo por professor: upload + contagens extraídas."""

from sqlmodel import Session, select, func

from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload, Orientacao, Producao, Projeto, Financiamento


def main() -> None:
    with Session(engine) as session:
        profs = session.exec(select(Professor).order_by(Professor.nome_completo)).all()
        print(f"{'Professor':<42} | {'PDF':<28} | {'Status':<22} | Ori | Prod | Proj")
        print("-" * 115)
        for pr in profs:
            upload = session.exec(
                select(CurriculoUpload)
                .where(CurriculoUpload.professor_id == pr.id)
                .order_by(CurriculoUpload.data_upload.desc())
            ).first()
            pdf = (upload.arquivo_nome[:28] if upload else "—") if upload else "sem PDF"
            status = (
                upload.status.value
                if upload and hasattr(upload.status, "value")
                else (str(upload.status) if upload else "—")
            )
            ori = session.exec(
                select(func.count())
                .select_from(Orientacao)
                .where(Orientacao.professor_id == pr.id)
            ).one()
            prod = session.exec(
                select(func.count())
                .select_from(Producao)
                .where(Producao.professor_id == pr.id)
            ).one()
            proj = session.exec(
                select(func.count())
                .select_from(Projeto)
                .where(Projeto.professor_id == pr.id)
            ).one()
            nome = (pr.nome_completo or "")[:42]
            flag = " ⚠️" if upload and "odlinari" in (upload.arquivo_nome or "").lower() and "camilla" in nome.lower() else ""
            print(f"{nome:<42} | {pdf:<28} | {status:<22} | {ori:3} | {prod:4} | {proj:3}{flag}")


if __name__ == "__main__":
    main()
