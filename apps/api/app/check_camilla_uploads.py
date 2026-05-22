from sqlmodel import Session, select, func

from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload, Orientacao, Producao, Projeto


def main() -> None:
    with Session(engine) as s:
        p = s.exec(
            select(Professor).where(Professor.email == "camilla.tavares@ufma.br")
        ).first()
        if not p:
            print("Camilla não encontrada")
            return
        uploads = s.exec(
            select(CurriculoUpload)
            .where(CurriculoUpload.professor_id == p.id)
            .order_by(CurriculoUpload.data_upload.desc())
        ).all()
        print(f"Professor: {p.nome_completo}\nUploads: {len(uploads)}\n")
        for u in uploads:
            ori = s.exec(
                select(func.count())
                .select_from(Orientacao)
                .where(Orientacao.curriculo_upload_id == u.id)
            ).one()
            prod = s.exec(
                select(func.count())
                .select_from(Producao)
                .where(Producao.curriculo_upload_id == u.id)
            ).one()
            proj = s.exec(
                select(func.count())
                .select_from(Projeto)
                .where(Projeto.curriculo_upload_id == u.id)
            ).one()
            print(
                f"  {u.data_upload} | {u.arquivo_nome[:40]} | status={u.status} | "
                f"ori={ori} prod={prod} proj={proj} | id={str(u.id)[:8]}..."
            )


if __name__ == "__main__":
    main()
