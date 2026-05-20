"""Diagnóstico rápido do docente Odlinari e uploads."""
import os
from sqlmodel import Session, select
from app.database import engine
from app.models.core import Professor
from app.models.data import CurriculoUpload

def main():
    with Session(engine) as s:
        p = s.exec(
            select(Professor).where(Professor.email.like("%odlinari%"))
        ).first()
        if not p:
            print("Professor Odlinari não encontrado")
            return
        print(f"Professor: {p.nome_completo} id={p.id}")
        uploads = s.exec(
            select(CurriculoUpload)
            .where(CurriculoUpload.professor_id == str(p.id))
            .order_by(CurriculoUpload.data_upload.desc())
        ).all()
        print(f"Uploads: {len(uploads)}")
        for u in uploads:
            print(f"  - {u.id} status={u.status} file={u.arquivo_nome}")
            print(f"    path={u.arquivo_url} exists={os.path.isfile(u.arquivo_url or '')}")
            print(f"    erro={u.mensagem_erro}")
    lattes = "/workspace/data/lattes"
    if os.path.isdir(lattes):
        files = [f for f in os.listdir(lattes) if "odlin" in f.lower() or "silva" in f.lower()]
        print("data/lattes odlinari-like:", files or "(nenhum)")
        print("total pdfs:", len([f for f in os.listdir(lattes) if f.lower().endswith(".pdf")]))

if __name__ == "__main__":
    main()
