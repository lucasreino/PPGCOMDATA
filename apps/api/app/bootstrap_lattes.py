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
from app.models.data import CurriculoUpload
from app.models.enums import StatusProcessamento, StatusValidacao
from app.services.pdf_processor import process_curriculo_pdf
from app.services.section_detector import split_and_save_sections
from app.services.ai_extractor import extract_and_save_section_data

# Root levels directories
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
        # 1. Get or create a default Research Line
        statement = select(LinhaPesquisa).where(LinhaPesquisa.nome == "Comunicação e Cultura Digital")
        linha = session.exec(statement).first()
        if not linha:
            print("Creating default research line...")
            linha = LinhaPesquisa(
                nome="Comunicação e Cultura Digital",
                descricao="Linha de pesquisa padrão para importação em lote."
            )
            session.add(linha)
            session.commit()
            session.refresh(linha)
            
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
            
            # Find or create professor
            stmt_prof = select(Professor).where(Professor.nome_completo == clean_name)
            prof = session.exec(stmt_prof).first()
            if not prof:
                print(f"👤 Docente '{clean_name}' não encontrado no banco. Criando registro...")
                prof = Professor(
                    nome_completo=clean_name,
                    linha_pesquisa_id=linha.id,
                    status=True
                )
                session.add(prof)
                session.commit()
                session.refresh(prof)
            else:
                print(f"👤 Docente '{clean_name}' já cadastrado.")

            # Copy PDF to backend storage
            unique_filename = f"{uuid.uuid4()}.pdf"
            dest_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
            src_path = os.path.join(LATTES_SRC_DIR, filename)
            
            try:
                shutil.copy2(src_path, dest_path)
            except Exception as e:
                print(f"❌ Erro ao copiar o arquivo para a pasta uploads: {e}")
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
                    continue
            except Exception as e:
                print(f"   ❌ Falha catastrófica ao processar PDF: {e}")
                continue
                
            # Step B: Section Splitting
            try:
                print("   [2/3] Particionando seções do currículo...")
                sections = split_and_save_sections(session, upload.id)
                if not sections:
                    print("   ⚠️ Nenhuma seção do Lattes reconhecida.")
                    continue
                print(f"   ✓ {len(sections)} seções detectadas com sucesso.")
            except Exception as e:
                print(f"   ❌ Falha ao particionar seções: {e}")
                continue
                
            # Step C: AI Extraction for each section
            try:
                print("   [3/3] Executando extração estruturada de entidades via IA...")
                ai_metrics = {
                    "projetos_extraidos": 0,
                    "eventos_extraidos": 0,
                    "producoes_extraidas": 0,
                    "financiamentos_extraidos": 0,
                    "lacunas_extraidas": 0
                }
                
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
                print(f"      - Lacunas: {ai_metrics['lacunas_extraidas']}")
                
            except Exception as e:
                print(f"   ❌ Erro durante extração de IA: {e}")
                continue
                
    print("\n" + "=" * 60)
    print("🏆 CARGA INICIAL COMPLETA!")
    print("Todos os Lattes foram processados e estão disponíveis no dashboard!")
    print("=" * 60)

if __name__ == "__main__":
    bootstrap()
