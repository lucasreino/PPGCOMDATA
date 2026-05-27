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
    scholar_user_id: Optional[str] = None
    scholar_citations_total: Optional[int] = None
    scholar_h_index: Optional[int] = None
    scholar_i10_index: Optional[int] = None
    scholar_metrics_since_year: Optional[int] = None
    scholar_profile_synced_at: Optional[str] = None

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
            scholar_user_id=getattr(professor, "scholar_user_id", None),
            scholar_citations_total=getattr(professor, "scholar_citations_total", None),
            scholar_h_index=getattr(professor, "scholar_h_index", None),
            scholar_i10_index=getattr(professor, "scholar_i10_index", None),
            scholar_metrics_since_year=getattr(
                professor, "scholar_metrics_since_year", None
            ),
            scholar_profile_synced_at=(
                professor.scholar_profile_synced_at.isoformat()
                if getattr(professor, "scholar_profile_synced_at", None)
                else None
            ),
        )
