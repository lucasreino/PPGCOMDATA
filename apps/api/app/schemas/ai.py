from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.enums import TipoProjeto, TipoFinanciamento, ConfiancaIA, GravidadeLacuna

class AIProjetoSchema(BaseModel):
    titulo: str = Field(description="Título do projeto de pesquisa, extensão ou desenvolvimento")
    tipo: TipoProjeto = Field(default=TipoProjeto.PESQUISA, description="Tipo de projeto")
    situacao: Optional[str] = Field(default=None, description="Situação do projeto (concluído, em andamento, etc.)")
    ano_inicio: Optional[int] = Field(default=None, description="Ano de início")
    ano_fim: Optional[int] = Field(default=None, description="Ano de término, se aplicável")
    descricao: Optional[str] = Field(default=None, description="Breve resumo ou descrição do projeto")
    papel_docente: Optional[str] = Field(default=None, description="Papel do professor (coordenador, integrante, etc.)")
    instituicoes: Optional[List[str]] = Field(default=None, description="Lista de instituições envolvidas no projeto")
    
    # Financial fields inferred
    financiamento_mencionado: bool = Field(default=False, description="True se houver menção explícita a financiamento no texto")
    agencia_fomento: Optional[str] = Field(default=None, description="Nome da agência de fomento se mencionada (ex: CNPq, FAPEMA)")
    
    # Quality metrics
    confianca_ia: ConfiancaIA = Field(default=ConfiancaIA.MEDIA, description="Confiança da IA na extração")
    trecho_original: str = Field(description="Trecho original do texto que fundamenta esta extração")
    observacoes: Optional[str] = Field(default=None, description="Notas ou observações adicionais")

class AIEventoSchema(BaseModel):
    nome_evento: str = Field(description="Nome completo do evento científico ou de extensão")
    ano: Optional[int] = Field(default=None, description="Ano de realização")
    cidade: Optional[str] = Field(default=None, description="Cidade de realização")
    pais: Optional[str] = Field(default=None, description="País de realização")
    tipo_participacao: Optional[str] = Field(default=None, description="Tipo de participação (apresentação de trabalho, palestra, ouvinte, etc.)")
    titulo_trabalho: Optional[str] = Field(default=None, description="Título do trabalho apresentado, se aplicável")
    
    financiamento_mencionado: bool = Field(default=False, description="True se houver menção a financiamento para ir ao evento")
    fonte_financiamento: Optional[str] = Field(default=None, description="Fonte de fomento mencionada (ex: auxílio viagem CAPES)")
    
    confianca_ia: ConfiancaIA = Field(default=ConfiancaIA.MEDIA, description="Confiança da IA")
    trecho_original: str = Field(description="Trecho do texto usado como evidência")
    observacoes: Optional[str] = Field(default=None, description="Outras notas")

class AIProducaoSchema(BaseModel):
    tipo: str = Field(description="Tipo de produção: artigo, livro, capitulo, anais, resumo, tecnica, outra")
    titulo: str = Field(description="Título completo da produção acadêmica")
    ano: Optional[int] = Field(default=None, description="Ano de publicação")
    veiculo: Optional[str] = Field(default=None, description="Veículo de publicação (Nome do Periódico, Editora, Evento, etc.)")
    doi: Optional[str] = Field(default=None, description="Código DOI se disponível")
    isbn: Optional[str] = Field(default=None, description="Código ISBN")
    issn: Optional[str] = Field(default=None, description="Código ISSN")
    evento_relacionado: Optional[str] = Field(default=None, description="Nome do evento se vinculado a anais")
    
    confianca_ia: ConfiancaIA = Field(default=ConfiancaIA.MEDIA, description="Confiança da IA")
    trecho_original: str = Field(description="Trecho original correspondente")
    observacoes: Optional[str] = Field(default=None, description="Observações")

class AIFinanciamentoSchema(BaseModel):
    tipo: TipoFinanciamento = Field(default=TipoFinanciamento.PESQUISA, description="Tipo de fomento (bolsa, auxílio, etc.)")
    fonte: Optional[str] = Field(default=None, description="Origem dos recursos (pública, privada, edital, UFMA, etc.)")
    agencia: Optional[str] = Field(default=None, description="Nome da agência de fomento (CAPES, CNPq, FAPEMA)")
    edital: Optional[str] = Field(default=None, description="Identificação do edital, se mencionado (ex: Edital Universal)")
    numero_processo: Optional[str] = Field(default=None, description="Número do processo administrativo")
    valor: Optional[str] = Field(default=None, description="Valor financeiro expressamente mencionado no texto")
    ano: Optional[int] = Field(default=None, description="Ano do fomento")
    vinculo_com: str = Field(default="projeto", description="O fomento está vinculado com: projeto, evento, producao ou desconhecido")
    
    confianca: ConfiancaIA = Field(default=ConfiancaIA.MEDIA, description="Confiança")
    trecho_original: str = Field(description="Trecho que comprova a menção")
    observacoes: Optional[str] = Field(default=None, description="Notas")

class AILacunaSchema(BaseModel):
    tipo_lacuna: str = Field(description="Categoria da lacuna: financiamento_incompleto, projeto_sem_ano, etc.")
    descricao: str = Field(description="Explicação detalhada da informação ausente no currículo")
    gravidade: GravidadeLacuna = Field(default=GravidadeLacuna.MEDIA, description="Gravidade da lacuna")
    acao_recomendada: Optional[str] = Field(default=None, description="Ação sugerida para a coordenação sanar a lacuna")
    trecho_original: Optional[str] = Field(default=None, description="Trecho onde se deduziu a ausência")

class LattesExtractionResultSchema(BaseModel):
    projetos: List[AIProjetoSchema] = Field(default_factory=list, description="Lista de projetos extraídos")
    eventos: List[AIEventoSchema] = Field(default_factory=list, description="Lista de eventos extraídos")
    producoes: List[AIProducaoSchema] = Field(default_factory=list, description="Lista de produções extraídas")
    financiamentos: List[AIFinanciamentoSchema] = Field(default_factory=list, description="Lista de financiamentos extraídos")
    lacunas: List[AILacunaSchema] = Field(default_factory=list, description="Lista de lacunas identificadas")
