from typing import Optional
from pydantic import BaseModel
from app.schemas.professor import ProfessorListItem


class ProfessorCatalogItem(ProfessorListItem):
    foto_url: Optional[str] = None
    titulacao_maxima: Optional[str] = None
    total_projetos: int = 0
    total_producoes: int = 0
    total_eventos: int = 0
    total_orientacoes: int = 0
    total_bancas: int = 0
    total_financiamentos: int = 0
