import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlmodel import Session, select
from app.models.data import CurriculoUpload, PdfPage, PdfSection

logger = logging.getLogger("ppgcomdata.section_detector")

# Standard Lattes section headers (case-insensitive regex patterns)
LATTES_SECTIONS_PATTERNS = {
    "Dados gerais": r"(?:^|\n)Dados gerais(?:\n|$)",
    "Formação acadêmica/titulação": r"(?:^|\n)Forma[cç]ã[o] acad[êe]mica/titula[cç]ã[o](?:\n|$)",
    "Atuação profissional": r"(?:^|\n)Atua[cç]ã[o] profissional(?:\n|$)",
    "Projetos de pesquisa": r"(?:^|\n)Projetos de pesquisa(?:\n|$)",
    "Projetos de extensão": r"(?:^|\n)Projetos de extensã[o](?:\n|$)",
    "Projetos de desenvolvimento": r"(?:^|\n)Projetos de desenvolvimento(?:\n|$)",
    "Produção bibliográfica": r"(?:^|\n)Produ[cç]ã[o] bibliogr[áa]fica(?:\n|$)",
    "Artigos completos publicados em periódicos": r"(?:^|\n)Artigos completos publicados em peri[óo]dicos(?:\n|$)",
    "Livros publicados/organizados": r"(?:^|\n)Livros publicados/organizados(?:\n|$)",
    "Capítulos de livros publicados": r"(?:^|\n)Cap[íi]tulos de livros publicados(?:\n|$)",
    "Trabalhos completos publicados em anais de congressos": r"(?:^|\n)Trabalhos completos publicados em anais(?:\n|$)",
    "Participação em eventos": r"(?:^|\n)Participa[cç]ã[o] em eventos(?:\s|/|$|\n)",
    "Organização de eventos": r"(?:^|\n)Organiza[cç]ã[o] de eventos(?:\s|/|$|\n)",
    "Produção técnica": r"(?:^|\n)Produ[cç]ã[o] t[ée]cnica(?:\s|$|\n)",
    "Orientações e supervisões em andamento": (
        r"(?:^|\n)Orienta[cç]õ[e]s e supervisõ[e]s em andamento"
    ),
    "Orientações e supervisões concluídas": (
        r"(?:^|\n)Orienta[cç]õ[e]s e supervisõ[e]s conclu[ií]das"
    ),
    "Orientações e supervisões": (
        r"(?:^|\n)Orienta[cç]õ[e]s e supervisõ[e]s(?!\s+(?:em andamento|conclu))"
    ),
    "Bancas": r"(?:^|\n)Bancas(?:\s|$|\n)",
    "Prêmios e títulos": r"(?:^|\n)Pr[êe]mios e t[íi]tulos(?:\n|$)"
}

def detect_sections(full_text: str) -> List[Dict[str, Any]]:
    """Analyzes the full text to detect start boundaries for standard sections.
    
    Returns:
        List of dicts representing detected boundaries, ordered by their occurrence.
    """
    boundaries = []
    
    for section_name, pattern in LATTES_SECTIONS_PATTERNS.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            boundaries.append({
                "nome_secao": section_name,
                "start_idx": match.start(),
                "end_idx": match.end()
            })
            
    boundaries.sort(key=lambda x: x["start_idx"])

    # Same start index: keep the more specific (longer) section title
    deduped: List[Dict[str, Any]] = []
    for boundary in boundaries:
        if deduped and deduped[-1]["start_idx"] == boundary["start_idx"]:
            if len(boundary["nome_secao"]) > len(deduped[-1]["nome_secao"]):
                deduped[-1] = boundary
        else:
            deduped.append(boundary)
    return deduped

def split_text_by_sections(full_text: str, boundaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Splits full text into chunks representing each detected section."""
    sections_chunks = []
    
    for i, boundary in enumerate(boundaries):
        start = boundary["start_idx"]
        # The section runs until the start of the next section, or the end of the text
        end = boundaries[i + 1]["start_idx"] if i + 1 < len(boundaries) else len(full_text)
        
        # Extract section content
        section_text = full_text[start:end].strip()
        
        sections_chunks.append({
            "nome_secao": boundary["nome_secao"],
            "texto_secao": section_text
        })
        
    return sections_chunks

def map_text_to_pages(
    pages: List[PdfPage], 
    section_text: str
) -> Tuple[int, int]:
    """Infers starting and ending page numbers of a section by searching where its snippet occurs."""
    # Find a small distinctive snippet from the start and end of the section text
    snippet_start = section_text[:150].strip()
    snippet_end = section_text[-150:].strip()
    
    start_page = 1
    end_page = len(pages)
    
    # Identify start page
    for page in pages:
        if snippet_start in page.texto:
            start_page = page.numero_pagina
            break
            
    # Identify end page
    for page in reversed(pages):
        if snippet_end in page.texto:
            end_page = page.numero_pagina
            break
            
    # Fallback sanity check
    if start_page > end_page:
        end_page = start_page
        
    return start_page, end_page

def split_and_save_sections(session: Session, curriculo_upload_id: str) -> List[PdfSection]:
    """Loads text from database, splits it by standard Lattes sections, and stores them in pdf_sections."""
    upload = session.get(CurriculoUpload, curriculo_upload_id)
    if not upload or not upload.texto_extraido:
        raise ValueError("Texto extraído não disponível para este upload.")
        
    logger.info(f"Iniciando identificação de seções para upload ID: {curriculo_upload_id}")
    
    # 1. Query pages to map sections back to page indices
    statement = select(PdfPage).where(PdfPage.curriculo_upload_id == curriculo_upload_id).order_by(PdfPage.numero_pagina)
    pages = session.exec(statement).all()
    
    # 2. Detect section boundaries and split
    boundaries = detect_sections(upload.texto_extraido)
    if not boundaries:
        logger.warning(f"Nenhuma seção detectada no texto do curriculo ID: {curriculo_upload_id}")
        return []
        
    chunks = split_text_by_sections(upload.texto_extraido, boundaries)
    db_sections = []
    
    # Delete any existing sections for this upload (idempotency)
    delete_statement = select(PdfSection).where(PdfSection.curriculo_upload_id == curriculo_upload_id)
    old_sections = session.exec(delete_statement).all()
    for os_sec in old_sections:
        session.delete(os_sec)
    session.commit()
    
    # 3. Save new sections
    for chunk in chunks:
        # Inferred start/end pages
        start_page, end_page = 1, 1
        if pages:
            start_page, end_page = map_text_to_pages(pages, chunk["texto_secao"])
            
        db_section = PdfSection(
            curriculo_upload_id=curriculo_upload_id,
            professor_id=upload.professor_id,
            nome_secao=chunk["nome_secao"],
            texto_secao=chunk["texto_secao"],
            pagina_inicio=start_page,
            pagina_fim=end_page,
            status_extracao=False
        )
        session.add(db_section)
        db_sections.append(db_section)
        
    session.commit()
    logger.info(f"{len(db_sections)} seções extraídas e salvas com sucesso.")
    return db_sections
