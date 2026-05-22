from typing import Optional
from pydantic import BaseModel
from app.models.enums import TipoDocente
from app.services.professor_foto import resolve_foto_url


class LinhaPesquisaBrief(BaseModel):
    id: str
    nome: str


class ProfessorListItem(BaseModel):
    id: str
    nome_completo: str
    nome_citacao: Optional[str] = None
    email: Optional[str] = None
    link_lattes: Optional[str] = None
    id_lattes: Optional[str] = None
    foto_url: Optional[str] = None
    titulacao_maxima: Optional[str] = None
    tipo_docente: TipoDocente
    status: bool
    linha_pesquisa_id: Optional[str] = None
    linha_pesquisa: Optional[LinhaPesquisaBrief] = None

    @classmethod
    def from_model(cls, professor) -> "ProfessorListItem":
        linha = None
        if professor.linha_pesquisa:
            linha = LinhaPesquisaBrief(
                id=str(professor.linha_pesquisa.id),
                nome=professor.linha_pesquisa.nome,
            )
        return cls(
            id=str(professor.id),
            nome_completo=professor.nome_completo,
            nome_citacao=professor.nome_citacao,
            email=professor.email,
            link_lattes=professor.link_lattes,
            id_lattes=professor.id_lattes,
            foto_url=getattr(professor, "foto_url", None)
            or resolve_foto_url(
                professor.nome_completo,
                professor.id_lattes,
                str(professor.id),
            ),
            titulacao_maxima=professor.titulacao_maxima,
            tipo_docente=professor.tipo_docente,
            status=professor.status,
            linha_pesquisa_id=str(professor.linha_pesquisa_id)
            if professor.linha_pesquisa_id
            else None,
            linha_pesquisa=linha,
        )
