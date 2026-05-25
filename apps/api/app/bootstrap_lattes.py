import os
import shutil
import uuid
import sys
from sqlmodel import Session, select

# Adjust path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.config import settings
from app.models.core import Professor, LinhaPesquisa
from app.services.professor_lookup import find_professor, normalize_text
from app.services.professor_oficial import get_official_professor_data
from app.models.data import CurriculoUpload
from app.models.enums import StatusProcessamento, StatusValidacao
from app.services.pdf_processor import process_curriculo_pdf
from app.services.section_detector import split_and_save_sections
from app.services.ai_extractor import extract_and_save_section_data
from app.services.upload_cleanup import clear_upload_extraction_data

# Root levels directories
if os.path.exists("/workspace/data/lattes"):
    LATTES_SRC_DIR = "/workspace/data/lattes"
else:
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    LATTES_SRC_DIR = os.path.join(ROOT_DIR, "data", "lattes")


def bootstrap():
    print("=" * 60)
    print("🚀 PPGCOMDATA - SCRIPT DE CARGA E BOOTSTRAP DE LATTES")
    print("=" * 60)
    
    if not os.path.exists(LATTES_SRC_DIR):
        print(f"❌ Pasta de origem não encontrada: {LATTES_SRC_DIR}")
        print("Criando a pasta vazia para você colocar os arquivos...")
        os.makedirs(LATTES_SRC_DIR, exist_ok=True)
        print(f"👉 Por favor, insira seus arquivos PDF em: {LATTES_SRC_DIR}")
        print("Em seguida, execute este script novamente.")
        return

    # List all PDFs
    pdf_files = [f for f in os.listdir(LATTES_SRC_DIR) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f"⚠️ Ninguém colocou nenhum arquivo PDF ainda na pasta: {LATTES_SRC_DIR}")
        print("👉 Insira os arquivos PDF correspondentes aos docentes e execute novamente.")
        return

    print(f"📁 Encontrado(s) {len(pdf_files)} arquivo(s) PDF para importar.")
    
    # Ensure local upload target directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    with Session(engine) as session:
        # 1. Get or create the two actual Research Lines
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
        
        stmt1 = select(LinhaPesquisa).where(LinhaPesquisa.nome == LINE1_NAME)
        linha1 = session.exec(stmt1).first()
        if not linha1:
            print(f"Creating Research Line 1: {LINE1_NAME}")
            linha1 = LinhaPesquisa(nome=LINE1_NAME, descricao=LINE1_DESC)
            session.add(linha1)
            
        stmt2 = select(LinhaPesquisa).where(LinhaPesquisa.nome == LINE2_NAME)
        linha2 = session.exec(stmt2).first()
        if not linha2:
            print(f"Creating Research Line 2: {LINE2_NAME}")
            linha2 = LinhaPesquisa(nome=LINE2_NAME, descricao=LINE2_DESC)
            session.add(linha2)
            
        session.commit()
        if linha1: session.refresh(linha1)
        if linha2: session.refresh(linha2)
            
        for filename in pdf_files:
            print("-" * 50)
            print(f"📄 Processando arquivo: {filename}")
            
            # Extract teacher name from file name
            # e.g., "Dr. Lucas Reino.pdf" -> "Lucas Reino" or "lucas_reino.pdf" -> "lucas reino"
            clean_name = os.path.splitext(filename)[0]
            clean_name = clean_name.replace("_", " ").replace("-", " ").strip()
            if clean_name.lower().startswith("dr. "):
                clean_name = clean_name[4:].strip()
            elif clean_name.lower().startswith("dra. "):
                clean_name = clean_name[5:].strip()
                
            clean_name = clean_name.title()
            
            # Decide which research line to map to based on teacher name keyword map
            name_lower = clean_name.lower()
            if any(k in name_lower for k in ["messias", "domingos", "izani", "larissa", "marcelli", "odlinari"]):
                assigned_line = linha1
            elif any(k in name_lower for k in ["tavares", "leila", "leticia", "thaisa", "gisa", "gislene", "thays", "michelly"]):
                assigned_line = linha2
            else:
                assigned_line = linha1 # default fallback
            
            prof = None
            nome_norm = normalize_text(clean_name)
            for official in get_official_professor_data():
                if normalize_text(official["nome_completo"]) == nome_norm:
                    prof = find_professor(
                        session,
                        nome_completo=official["nome_completo"],
                        email=official["email"],
                        id_lattes=official.get("id_lattes"),
                    )
                    break
            if not prof:
                for official in get_official_professor_data():
                    official_norm = normalize_text(official["nome_completo"])
                    if nome_norm in official_norm or official_norm in nome_norm:
                        prof = find_professor(
                            session,
                            email=official["email"],
                            id_lattes=official.get("id_lattes"),
                        )
                        break
            if not prof:
                prof = find_professor(session, nome_completo=clean_name)

            if not prof:
                print(f"👤 Docente '{clean_name}' não encontrado no banco. Criando registro...")
                prof = Professor(
                    nome_completo=clean_name,
                    linha_pesquisa_id=assigned_line.id if assigned_line else None,
                    status=True,
                )
                session.add(prof)
                session.commit()
                session.refresh(prof)
            else:
                print(f"👤 Docente vinculado: {prof.nome_completo}")
                # Update research line if it is None or set to old default
                if not prof.linha_pesquisa_id:
                    prof.linha_pesquisa_id = assigned_line.id if assigned_line else None
                    session.add(prof)
                    session.commit()

            # Copy PDF to backend storage
            unique_filename = f"{uuid.uuid4()}.pdf"
            dest_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
            src_path = os.path.join(LATTES_SRC_DIR, filename)
            
            try:
                shutil.copy2(src_path, dest_path)
            except Exception as e:
                print(f"❌ Erro ao copiar o arquivo para a pasta uploads: {e}")
                session.rollback()
                continue
                
            # Create upload database entry
            upload = CurriculoUpload(
                professor_id=prof.id,
                arquivo_url=dest_path,
                arquivo_nome=filename,
                status=StatusProcessamento.AGUARDANDO_PROCESSAMENTO
            )
            session.add(upload)
            session.commit()
            session.refresh(upload)
            
            print(f"⚙️ Iniciando pipeline de processamento para '{clean_name}'...")
            
            # Step A: PDF Page Extraction
            try:
                print("   [1/3] Extraindo páginas de texto via PyMuPDF...")
                upload = process_curriculo_pdf(session, upload.id)
                if upload.status == StatusProcessamento.ERRO_NO_PROCESSAMENTO:
                    print(f"   ❌ Falha na extração de texto: {upload.mensagem_erro}")
                    session.rollback()
                    continue
            except Exception as e:
                print(f"   ❌ Falha catastrófica ao processar PDF: {e}")
                session.rollback()
                continue
                
            # Step B: Section Splitting
            try:
                print("   [2/3] Particionando seções do currículo...")
                sections = split_and_save_sections(session, upload.id)
                if not sections:
                    print("   ⚠️ Nenhuma seção do Lattes reconhecida.")
                    session.rollback()
                    continue
                print(f"   ✓ {len(sections)} seções detectadas com sucesso.")
            except Exception as e:
                print(f"   ❌ Falha ao particionar seções: {e}")
                session.rollback()
                continue
                
            # Step C: AI Extraction for each section
            try:
                print("   [3/3] Executando extração estruturada de entidades via IA...")
                ai_metrics = {
                    "projetos_extraidos": 0,
                    "eventos_extraidos": 0,
                    "producoes_extraidas": 0,
                    "financiamentos_extraidos": 0,
                    "formacoes_extraidas": 0,
                    "orientacoes_extraidas": 0,
                    "bancas_extraidas": 0,
                    "perfis_extraidos": 0,
                    "lacunas_extraidas": 0,
                }
                
                clear_upload_extraction_data(session, upload.id)
                for section in sections:
                    metrics = extract_and_save_section_data(session, section.id)
                    for key in ai_metrics:
                        ai_metrics[key] += metrics.get(key, 0)
                        
                # Update status
                upload.status = StatusProcessamento.VALIDADO
                session.add(upload)
                session.commit()
                
                print(f"   🎉 Extração bem-sucedida para '{clean_name}'!")
                print(f"      - Projetos: {ai_metrics['projetos_extraidos']}")
                print(f"      - Eventos: {ai_metrics['eventos_extraidos']}")
                print(f"      - Produções: {ai_metrics['producoes_extraidas']}")
                print(f"      - Financiamentos: {ai_metrics['financiamentos_extraidos']}")
                print(f"      - Formações: {ai_metrics['formacoes_extraidas']}")
                print(f"      - Orientações: {ai_metrics['orientacoes_extraidas']}")
                print(f"      - Bancas: {ai_metrics['bancas_extraidas']}")
                print(f"      - Lacunas: {ai_metrics['lacunas_extraidas']}")
                
            except Exception as e:
                print(f"   ❌ Erro durante extração de IA: {e}")
                session.rollback()
                continue
                
    print("\n" + "=" * 60)
    print("🏆 CARGA INICIAL COMPLETA!")
    print("Todos os Lattes foram processados e estão disponíveis no dashboard!")
    print("=" * 60)

if __name__ == "__main__":
    bootstrap()
