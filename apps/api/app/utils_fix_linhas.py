import os
import sys
from sqlmodel import Session, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models.core import Professor, LinhaPesquisa
from app.models.data import Projeto, Producao

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

KEYWORDS_LINE1 = [
    "tecnologia", "audiovisual", "regional", "digital", "internet", "plataforma", "algoritmo",
    "rede", "computador", "som", "radio", "rádio", "cinema", "filme", "televisao", "televisão",
    "tv", "game", "jogo", "midiatica", "midiática", "web", "virtual", "software", "aplicativo"
]

KEYWORDS_LINE2 = [
    "cidadania", "identidade", "gênero", "genero", "social", "jornalismo", "jornalista",
    "representação", "representacao", "discurso", "narrativa", "negociação", "negociacao",
    "democracia", "politica", "política", "publico", "público", "movimento", "cultura",
    "recepção", "recepcao", "consumo", "audiência", "audiencia", "mulher", "negro", "raça"
]

def run_analysis_and_seeding():
    with Session(engine) as session:
        print("--- seeding new research lines ---")
        # Ensure Line 1
        stmt1 = select(LinhaPesquisa).where(LinhaPesquisa.nome == LINE1_NAME)
        l1 = session.exec(stmt1).first()
        if not l1:
            print(f"Creating Line 1: {LINE1_NAME}")
            l1 = LinhaPesquisa(nome=LINE1_NAME, descricao=LINE1_DESC)
            session.add(l1)
        else:
            print(f"Line 1 already exists: {LINE1_NAME}")
            l1.descricao = LINE1_DESC
            session.add(l1)

        # Ensure Line 2
        stmt2 = select(LinhaPesquisa).where(LinhaPesquisa.nome == LINE2_NAME)
        l2 = session.exec(stmt2).first()
        if not l2:
            print(f"Creating Line 2: {LINE2_NAME}")
            l2 = LinhaPesquisa(nome=LINE2_NAME, descricao=LINE2_DESC)
            session.add(l2)
        else:
            print(f"Line 2 already exists: {LINE2_NAME}")
            l2.descricao = LINE2_DESC
            session.add(l2)

        session.commit()
        session.refresh(l1)
        session.refresh(l2)

        # List all professors
        profs = session.exec(select(Professor)).all()
        print(f"\n--- Analyzing {len(profs)} professors ---")
        
        for p in profs:
            # Gather text from projects and productions
            proj_stmt = select(Projeto).where(Projeto.professor_id == p.id)
            projs = session.exec(proj_stmt).all()
            
            prod_stmt = select(Producao).where(Producao.professor_id == p.id)
            prods = session.exec(prod_stmt).all()
            
            combined_text = " ".join([p.nome_completo])
            for pr in projs:
                combined_text += f" {pr.titulo} {pr.descricao or ''}"
            for pd in prods:
                combined_text += f" {pd.titulo} {pd.veiculo or ''}"
                
            combined_text = combined_text.lower()
            
            # Count keyword hits
            score_l1 = sum(combined_text.count(k) for k in KEYWORDS_LINE1)
            score_l2 = sum(combined_text.count(k) for k in KEYWORDS_LINE2)
            
            # Assign line
            assigned_line = l1 if score_l1 >= score_l2 else l2
            
            # Specific manual overrides for better accuracy based on PPGCOM alignments:
            # Let's adjust manually if the automated score is close or needs alignment
            name_lower = p.nome_completo.lower()
            if "messias" in name_lower or "domingos" in name_lower or "izani" in name_lower:
                assigned_line = l1
            elif "tavares" in name_lower or "larissa" in name_lower or "marcelli" in name_lower:
                assigned_line = l2
            
            print(f"Docente: {p.nome_completo:<30} | Score L1: {score_l1:<3} | Score L2: {score_l2:<3} | Assigned: {assigned_line.nome}")
            
            p.linha_pesquisa_id = assigned_line.id
            session.add(p)
            
        session.commit()
        print("\n--- Migration Completed successfully! ---")

        # Optionally cleanup old line
        cleanup_stmt = select(LinhaPesquisa).where(LinhaPesquisa.nome == "Comunicação e Cultura Digital")
        old_l = session.exec(cleanup_stmt).first()
        if old_l:
            print("Cleaning up old 'Comunicação e Cultura Digital' line of research...")
            session.delete(old_l)
            session.commit()
            print("Cleanup completed.")

if __name__ == "__main__":
    run_analysis_and_seeding()
