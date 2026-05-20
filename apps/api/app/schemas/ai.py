from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.enums import (
    TipoProjeto,
    TipoFinanciamento,
    ConfiancaIA,
    GravidadeLacuna,
    NivelFormacao,
    TipoOrientacao,
    StatusOrientacao,
    PapelOrientacao,
    TipoBanca,
    NivelBanca,
    PapelBanca,
    EscopoEvento,
    TipoProducaoTecnica,
    TipoPremio,
    PapelGrupoPesquisa,
)

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
    eh_organizacao: bool = Field(default=False, description="True se for organização do evento, não participação")
    escopo: Optional[EscopoEvento] = Field(default=None, description="nacional ou internacional")
    instituicao_promotora: Optional[str] = Field(default=None, description="Instituição promotora do evento")

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
    autores: Optional[str] = Field(default=None, description="Lista de autores como no texto")
    qualis: Optional[str] = Field(default=None, description="Estrato Qualis se citado (A1, A2, B1, etc.)")
    idioma: Optional[str] = Field(default=None, description="Idioma da publicação")
    indexadores: Optional[str] = Field(default=None, description="Indexadores citados (Scopus, WoS, etc.)")
    volume: Optional[str] = Field(default=None, description="Volume do periódico")
    paginas: Optional[str] = Field(default=None, description="Páginas")
    eh_primeiro_autor: Optional[bool] = Field(
        default=None, description="True se o docente do currículo for primeiro autor"
    )

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

class AIFormacaoSchema(BaseModel):
    nivel: NivelFormacao = Field(default=NivelFormacao.OUTRA)
    curso: Optional[str] = None
    instituicao: Optional[str] = None
    ano_inicio: Optional[int] = None
    ano_fim: Optional[int] = None
    area_conhecimento: Optional[str] = None
    pais: Optional[str] = None
    periodo_sanduiche: bool = False
    instituicao_exterior: Optional[str] = None
    confianca_ia: ConfiancaIA = ConfiancaIA.MEDIA
    trecho_original: str = Field(description="Trecho que comprova a titulação")

class AIOrientacaoSchema(BaseModel):
    tipo: TipoOrientacao = TipoOrientacao.OUTRA
    status: StatusOrientacao = StatusOrientacao.CONCLUIDA
    nome_orientando: Optional[str] = None
    titulo_trabalho: Optional[str] = None
    instituicao: Optional[str] = None
    ano_inicio: Optional[int] = None
    ano_conclusao: Optional[int] = None
    papel: PapelOrientacao = PapelOrientacao.ORIENTADOR
    confianca_ia: ConfiancaIA = ConfiancaIA.MEDIA
    trecho_original: str = Field(description="Trecho que comprova a orientação")
    observacoes: Optional[str] = None

class AIBancaSchema(BaseModel):
    tipo: TipoBanca = TipoBanca.OUTRA
    nivel: NivelBanca = NivelBanca.OUTRO
    nome_candidato: Optional[str] = None
    titulo_trabalho: Optional[str] = None
    instituicao: Optional[str] = None
    ano: Optional[int] = None
    papel: PapelBanca = PapelBanca.MEMBRO
    confianca_ia: ConfiancaIA = ConfiancaIA.MEDIA
    trecho_original: str = Field(description="Trecho que comprova a banca")
    observacoes: Optional[str] = None

class AIPerfilSchema(BaseModel):
    data_ultima_atualizacao: Optional[str] = Field(
        default=None, description="Data no formato AAAA-MM-DD se explícita"
    )
    resumo_cv: Optional[str] = None
    palavras_chave: Optional[List[str]] = None
    nome_citacao: Optional[str] = None
    link_orcid: Optional[str] = None
    confianca_ia: ConfiancaIA = ConfiancaIA.MEDIA
    trecho_original: Optional[str] = None

class LattesExtractionResultSchema(BaseModel):
    projetos: List[AIProjetoSchema] = Field(default_factory=list, description="Lista de projetos extraídos")
    eventos: List[AIEventoSchema] = Field(default_factory=list, description="Lista de eventos extraídos")
    producoes: List[AIProducaoSchema] = Field(default_factory=list, description="Lista de produções extraídas")
    financiamentos: List[AIFinanciamentoSchema] = Field(default_factory=list, description="Lista de financiamentos extraídos")
    lacunas: List[AILacunaSchema] = Field(default_factory=list, description="Lista de lacunas identificadas")


class FormacaoExtractionSchema(BaseModel):
    formacoes: List[AIFormacaoSchema] = Field(default_factory=list)
    lacunas: List[AILacunaSchema] = Field(default_factory=list)


class OrientacaoExtractionSchema(BaseModel):
    orientacoes: List[AIOrientacaoSchema] = Field(default_factory=list)
    lacunas: List[AILacunaSchema] = Field(default_factory=list)


class BancaExtractionSchema(BaseModel):
    bancas: List[AIBancaSchema] = Field(default_factory=list)
    lacunas: List[AILacunaSchema] = Field(default_factory=list)


class PerfilExtractionSchema(BaseModel):
    perfil: Optional[AIPerfilSchema] = None
    lacunas: List[AILacunaSchema] = Field(default_factory=list)


class EventosExtractionSchema(BaseModel):
    eventos: List[AIEventoSchema] = Field(default_factory=list)
    lacunas: List[AILacunaSchema] = Field(default_factory=list)


class AIProducaoTecnicaSchema(BaseModel):
    tipo: TipoProducaoTecnica = TipoProducaoTecnica.OUTRA
    titulo: str
    ano: Optional[int] = None
    instituicao: Optional[str] = None
    descricao: Optional[str] = None
    url: Optional[str] = None
    confianca_ia: ConfiancaIA = ConfiancaIA.MEDIA
    trecho_original: str


class ProducaoTecnicaExtractionSchema(BaseModel):
    producoes_tecnicas: List[AIProducaoTecnicaSchema] = Field(default_factory=list)
    lacunas: List[AILacunaSchema] = Field(default_factory=list)


class AIPremioSchema(BaseModel):
    tipo: TipoPremio = TipoPremio.OUTRO
    nome: str
    ano: Optional[int] = None
    instituicao_concedente: Optional[str] = None
    descricao: Optional[str] = None
    confianca_ia: ConfiancaIA = ConfiancaIA.MEDIA
    trecho_original: str


class PremiosExtractionSchema(BaseModel):
    premios: List[AIPremioSchema] = Field(default_factory=list)
    lacunas: List[AILacunaSchema] = Field(default_factory=list)


class AIGrupoPesquisaSchema(BaseModel):
    nome_grupo: str
    codigo_dgp: Optional[str] = None
    papel: PapelGrupoPesquisa = PapelGrupoPesquisa.MEMBRO
    linha_tematica: Optional[str] = None
    instituicao: Optional[str] = None
    confianca_ia: ConfiancaIA = ConfiancaIA.MEDIA
    trecho_original: str


class GruposPesquisaExtractionSchema(BaseModel):
    grupos: List[AIGrupoPesquisaSchema] = Field(default_factory=list)
    lacunas: List[AILacunaSchema] = Field(default_factory=list)
