from typing import Optional
from pydantic import BaseModel
from app.models.enums import TipoProjeto, TipoImpactoProjeto, TipoRecurso


class RelatorioProjetoCreate(BaseModel):
    professor_id: str
    titulo: str
    tipo: TipoProjeto = TipoProjeto.EXTENSAO
    linha_pesquisa_id: Optional[str] = None
    resumo: Optional[str] = None
    impacto_social: Optional[str] = None
    tema_principal: Optional[str] = None
    publico_atendido: Optional[str] = None
    territorio_impactado: Optional[str] = None
    ods_relacionado: Optional[str] = None
    produto_gerado: Optional[str] = None
    tipo_impacto: Optional[TipoImpactoProjeto] = None
    possui_financiamento_confirmado: Optional[bool] = None
    houve_financiamento: bool = False
    agencia: Optional[str] = None
    valor_aprovado: Optional[float] = None
    valor_executado: Optional[float] = None


class RelatorioProjetoUpdate(BaseModel):
    titulo: Optional[str] = None
    tipo: Optional[TipoProjeto] = None
    resumo: Optional[str] = None
    impacto_social: Optional[str] = None
    tema_principal: Optional[str] = None
    publico_atendido: Optional[str] = None
    territorio_impactado: Optional[str] = None
    ods_relacionado: Optional[str] = None
    produto_gerado: Optional[str] = None
    tipo_impacto: Optional[TipoImpactoProjeto] = None
    possui_financiamento_confirmado: Optional[bool] = None
