from typing import List, Optional
from pydantic import BaseModel


class OrientacaoResumoItem(BaseModel):
    id: str
    tipo: str
    status: str
    nome_orientando: Optional[str] = None
    titulo_trabalho: Optional[str] = None
    ano_conclusao: Optional[int] = None
    status_validacao: str


class FormacaoResumoItem(BaseModel):
    id: str
    nivel: str
    curso: Optional[str] = None
    instituicao: Optional[str] = None
    ano_fim: Optional[int] = None
    status_validacao: str


class ProfessorResumoAcademico(BaseModel):
    professor_id: str
    titulacao_maxima: Optional[str] = None
    data_ultima_atualizacao_lattes: Optional[str] = None
    total_orientacoes: int
    orientacoes_concluidas: int
    orientacoes_em_andamento: int
    orientacoes_ultimos_5_anos: int
    total_bancas: int
    total_formacoes: int
    orientacoes: List[OrientacaoResumoItem] = []
    formacoes: List[FormacaoResumoItem] = []
