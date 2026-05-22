"""Atualiza foto_url dos professores a partir de data/fotos. Execute: python -m app.sync_foto_urls"""

import os
import sys

from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.core import Professor
from app.services.professor_foto import resolve_foto_url, fotos_dir


def main() -> None:
    base = fotos_dir()
    print(f"Diretório de fotos: {base}")
    with Session(engine) as session:
        profs = session.exec(select(Professor).order_by(Professor.nome_completo)).all()
        updated = 0
        for prof in profs:
            url = resolve_foto_url(
                prof.nome_completo,
                prof.id_lattes,
                str(prof.id),
            )
            if url and prof.foto_url != url:
                prof.foto_url = url
                session.add(prof)
                updated += 1
                print(f"  {prof.nome_completo}: {url}")
            elif url:
                print(f"  OK {prof.nome_completo}")
            else:
                print(f"  — sem foto: {prof.nome_completo}")
        session.commit()
    print(f"\nAtualizados: {updated}")


if __name__ == "__main__":
    main()
