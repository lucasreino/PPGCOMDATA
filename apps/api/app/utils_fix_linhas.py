import os
import sys
from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.core import Professor, LinhaPesquisa

# Define correct lines
LINE1_NAME = "Tecnologias, Audiovisual e Processos Regionais de Comunicação"
LINE2_NAME = "Processos Comunicacionais, Cidadania e Identidades"

LINE1_DESC = (
    "As pesquisas desta linha tem como foco explorar as implicações das tecnologias de comunicação "
    "e do audiovisual nos processos comunicacionais em diversos contextos. A investigação abrange "
    "o impacto das novas tecnologias, como a internet e plataformas digitais, na transformação da "
    "produção e distribuição de conteúdo, além de analisar as práticas de consumo e as novas formas "
    "de interação que surgem com esses avanços. Por outro lado, a linha também examina os processos "
    "comunicacionais em nível regional, investigando como as dinâmicas locais influenciam a construção "
    "de narrativas e a representação cultural."
)

LINE2_DESC = (
    "Esta linha contempla pesquisas que se dedicam a investigar as relações entre os fluxos "
    "de comunicação e a formação das identidades sociais e culturais, com especial atenção aos "
    "processos de construção e negociação da cidadania em contextos contemporâneos."
)

PROFESSOR_DATA = {
    # LINHA 1
    "izani": {
        "nome_completo": "Izani Pibernat Mustafá",
        "email": "izani.mustafa@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/9088752631596667",
        "id_lattes": "9088752631596667",
        "linha": "linha1"
    },
    "messias": {
        "nome_completo": "José Carlos Messias Santos Franco",
        "email": "jose.cmsf@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/8042448829229400",
        "id_lattes": "8042448829229400",
        "linha": "linha1"
    },
    "larissa": {
        "nome_completo": "Larissa Leda Fonseca Rocha",
        "email": "larissa.leda@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/5812508596685080",
        "id_lattes": "5812508596685080",
        "linha": "linha1"
    },
    "marcelli": {
        "nome_completo": "Marcelli Alves da Silva",
        "email": "marcelli.alves@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/8985071802390376",
        "id_lattes": "8985071802390376",
        "linha": "linha1"
    },
    "domingos": {
        "nome_completo": "Domingos Alves de Almeida",
        "email": "domingos.almeida@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/1919610825042640",
        "id_lattes": "1919610825042640",
        "linha": "linha1"
    },
    "odlinari": {
        "nome_completo": "Odlinari Ramon Nascimento da Silva",
        "email": "odlinari.silva@ufma.br",
        "link_lattes": "https://lattes.cnpq.br/4303555424897191",
        "id_lattes": "4303555424897191",
        "linha": "linha1"
    },
    # LINHA 2
    "tavares": {
        "nome_completo": "Camilla Quesada Tavares",
        "email": "camilla.tavares@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/1766143822703684",
        "id_lattes": "1766143822703684",
        "linha": "linha2"
    },
    "leila": {
        "nome_completo": "Leila Lima de Sousa",
        "email": "sousa.leila@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/9312604992263679",
        "id_lattes": "9312604992263679",
        "linha": "linha2"
    },
    "leticia": {
        "nome_completo": "Letícia Conceição Martins Cardoso",
        "email": "leticia.cardoso@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/6186532880175192",
        "id_lattes": "6186532880175192",
        "linha": "linha2"
    },
    "thaisa": {
        "nome_completo": "Thaisa Cristina Bueno",
        "email": "thaisa.bueno@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/4123207392983951",
        "id_lattes": "4123207392983951",
        "linha": "linha2"
    },
    "gislene": {
        "nome_completo": "Maria Gislene Carvalho Fonseca",
        "email": "maria.gcf@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/4061348210902950",
        "id_lattes": "4061348210902950",
        "linha": "linha2"
    },
    "gisa": {
        "nome_completo": "Maria Gislene Carvalho Fonseca",
        "email": "maria.gcf@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/4061348210902950",
        "id_lattes": "4061348210902950",
        "linha": "linha2"
    },
    "thays": {
        "nome_completo": "Thays Assunção Reis",
        "email": "thays.assuncao@ufma.br",
        "link_lattes": "http://lattes.cnpq.br/7896667981420340",
        "id_lattes": "7896667981420340",
        "linha": "linha2"
    },
    "michelly": {
        "nome_completo": "Michelly Santos de Carvalho",
        "email": "michelly.carvalho@ufma.br",
        "link_lattes": "https://lattes.cnpq.br/0079215403799516",
        "id_lattes": "0079215403799516",
        "linha": "linha2"
    }
}

def run_precision_seeding():
    with Session(engine) as session:
        print("--- seeding research lines ---")
        # Ensure Line 1
        stmt1 = select(LinhaPesquisa).where(LinhaPesquisa.nome == LINE1_NAME)
        l1 = session.exec(stmt1).first()
        if not l1:
            l1 = LinhaPesquisa(nome=LINE1_NAME, descricao=LINE1_DESC)
            session.add(l1)
        else:
            l1.descricao = LINE1_DESC
            session.add(l1)

        # Ensure Line 2
        stmt2 = select(LinhaPesquisa).where(LinhaPesquisa.nome == LINE2_NAME)
        l2 = session.exec(stmt2).first()
        if not l2:
            l2 = LinhaPesquisa(nome=LINE2_NAME, descricao=LINE2_DESC)
            session.add(l2)
        else:
            l2.descricao = LINE2_DESC
            session.add(l2)

        session.commit()
        session.refresh(l1)
        session.refresh(l2)

        # Update existing professors
        profs = session.exec(select(Professor)).all()
        matched_keys = set()
        
        print("\n--- Updating existing professors ---")
        for p in profs:
            name_lower = p.nome_completo.lower()
            matched = False
            for key, data in PROFESSOR_DATA.items():
                if key in name_lower:
                    print(f"Updating professor data: '{p.nome_completo}' -> '{data['nome_completo']}'")
                    p.nome_completo = data["nome_completo"]
                    p.email = data["email"]
                    p.link_lattes = data["link_lattes"]
                    p.id_lattes = data["id_lattes"]
                    p.linha_pesquisa_id = l1.id if data["linha"] == "linha1" else l2.id
                    session.add(p)
                    matched_keys.add(key)
                    matched = True
                    break
            if not matched:
                print(f"⚠️ Unmatched database professor: {p.nome_completo}")

        # Create new/missing professors
        print("\n--- Seeding missing professors ---")
        for key, data in PROFESSOR_DATA.items():
            if key not in matched_keys:
                # Check if the professor already exists under the new full name to avoid duplicate seeds
                stmt = select(Professor).where(Professor.nome_completo == data["nome_completo"])
                existing = session.exec(stmt).first()
                if not existing:
                    print(f"Creating missing professor: '{data['nome_completo']}'")
                    new_p = Professor(
                        nome_completo=data["nome_completo"],
                        email=data["email"],
                        link_lattes=data["link_lattes"],
                        id_lattes=data["id_lattes"],
                        linha_pesquisa_id=l1.id if data["linha"] == "linha1" else l2.id,
                        status=True
                    )
                    session.add(new_p)
                else:
                    print(f"Professor already exists under full name: '{data['nome_completo']}'")

        session.commit()
        print("\n--- Precision Migration Completed! ---")

        # Cleanup old line if still exists
        cleanup_stmt = select(LinhaPesquisa).where(LinhaPesquisa.nome == "Comunicação e Cultura Digital")
        old_l = session.exec(cleanup_stmt).first()
        if old_l:
            print("Cleaning up old 'Comunicação e Cultura Digital' line...")
            session.delete(old_l)
            session.commit()
            print("Old line cleanup completed.")

if __name__ == "__main__":
    run_precision_seeding()
