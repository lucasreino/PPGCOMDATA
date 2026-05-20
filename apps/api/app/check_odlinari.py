"""Diagnóstico rápido do docente Odlinari e uploads."""
import os
from sqlmodel import Session, select
from app.database import engine
from app.models.core import Professor
from sqlmodel import func
from app.models.data import CurriculoUpload, Orientacao, Producao, Projeto, Financiamento

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
        pid = str(p.id)
        for label, model in (
            ("orientacoes", Orientacao),
            ("producoes", Producao),
            ("projetos", Projeto),
            ("financiamentos", Financiamento),
        ):
            n = s.exec(
                select(func.count()).select_from(model).where(model.professor_id == pid)
            ).one()
            print(f"  {label}: {n}")
        oris = s.exec(
            select(Orientacao).where(Orientacao.professor_id == pid).limit(8)
        ).all()
        for o in oris:
            print(f"    orientando: {o.nome_orientando} | {o.nivel} | {o.status}")
        upload_id = uploads[0].id if uploads else None
        if upload_id:
            linked = s.exec(
                select(Producao).where(Producao.curriculo_upload_id == upload_id).limit(1)
            ).first()
            print(f"  dados vinculados ao upload atual: {'sim' if linked else 'nao'}")
        print(
            "  interpretacao: PROCESSADO_COM_SUCESSO = texto PDF ok; "
            "IA completa => aguardando_validacao ou validado"
        )
    lattes = "/workspace/data/lattes"
    if os.path.isdir(lattes):
        files = [f for f in os.listdir(lattes) if "odlin" in f.lower() or "silva" in f.lower()]
        print("data/lattes odlinari-like:", files or "(nenhum)")
        print("total pdfs:", len([f for f in os.listdir(lattes) if f.lower().endswith(".pdf")]))

if __name__ == "__main__":
    main()
