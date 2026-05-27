from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import Column, Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel
from app.models.base import UUIDModel, TimestampModel
from app.models.enums import (
    StatusProcessamento, StatusValidacao, TipoProjeto, TipoFinanciamento,
    ConfiancaIA, GravidadeLacuna, TipoRecurso, FonteDado,
    NivelFormacao, TipoOrientacao, StatusOrientacao, PapelOrientacao,
    TipoBanca, NivelBanca, PapelBanca, EscopoEvento,
    TipoProducaoTecnica, TipoPremio, PapelGrupoPesquisa,
    StatusTratamentoLacuna, TipoImpactoProjeto,
)
from app.models.core import Professor, LinhaPesquisa

class CurriculoUpload(UUIDModel, TimestampModel, table=True):
    __tablename__ = "curriculo_uploads"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    arquivo_url: str = Field(nullable=False)
    arquivo_nome: str = Field(nullable=False)
    ano_inicio: Optional[int] = Field(default=None, nullable=True)
    ano_fim: Optional[int] = Field(default=None, nullable=True)
    status: StatusProcessamento = Field(default=StatusProcessamento.AGUARDANDO_PROCESSAMENTO, index=True, nullable=False)
    texto_extraido: Optional[str] = Field(default=None, nullable=True)
    data_upload: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    data_processamento: Optional[datetime] = Field(default=None, nullable=True)
    mensagem_erro: Optional[str] = Field(default=None, nullable=True)

    # Relationships
    professor: Professor = Relationship(back_populates="uploads")
    pdf_pages: List["PdfPage"] = Relationship(back_populates="upload")
    pdf_sections: List["PdfSection"] = Relationship(back_populates="upload")
    projetos: List["Projeto"] = Relationship(back_populates="upload")
    eventos: List["Evento"] = Relationship(back_populates="upload")
    producoes: List["Producao"] = Relationship(back_populates="upload")
    alertas_lacunas: List["AlertaLacuna"] = Relationship(back_populates="upload")
    formacoes: List["FormacaoAcademica"] = Relationship(back_populates="upload")
    orientacoes: List["Orientacao"] = Relationship(back_populates="upload")
    bancas: List["Banca"] = Relationship(back_populates="upload")
    perfis_lattes: List["PerfilLattes"] = Relationship(back_populates="upload")
    producoes_tecnicas: List["ProducaoTecnica"] = Relationship(back_populates="upload")
    premios: List["PremioTitulo"] = Relationship(back_populates="upload")
    grupos_pesquisa: List["GrupoPesquisaDocente"] = Relationship(back_populates="upload")

class PdfPage(UUIDModel, table=True):
    __tablename__ = "pdf_pages"

    curriculo_upload_id: str = Field(foreign_key="curriculo_uploads.id", index=True, nullable=False)
    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    numero_pagina: int = Field(nullable=False)
    texto: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    upload: CurriculoUpload = Relationship(back_populates="pdf_pages")
    professor: Professor = Relationship(back_populates="pdf_pages")

class PdfSection(UUIDModel, table=True):
    __tablename__ = "pdf_sections"

    curriculo_upload_id: str = Field(foreign_key="curriculo_uploads.id", index=True, nullable=False)
    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    nome_secao: str = Field(nullable=False, index=True)
    texto_secao: str = Field(nullable=False)
    pagina_inicio: int = Field(nullable=False)
    pagina_fim: int = Field(nullable=False)
    status_extracao: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    upload: CurriculoUpload = Relationship(back_populates="pdf_sections")
    professor: Professor = Relationship(back_populates="pdf_sections")

class Projeto(UUIDModel, TimestampModel, table=True):
    __tablename__ = "projetos"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    curriculo_upload_id: Optional[str] = Field(default=None, foreign_key="curriculo_uploads.id", index=True, nullable=True)
    
    titulo: str = Field(nullable=False, index=True)
    tipo: TipoProjeto = Field(default=TipoProjeto.PESQUISA, index=True, nullable=False)
    situacao: Optional[str] = Field(default=None, nullable=True)
    ano_inicio: Optional[int] = Field(default=None, index=True, nullable=True)
    ano_fim: Optional[int] = Field(default=None, index=True, nullable=True)
    descricao: Optional[str] = Field(default=None, nullable=True)
    papel_docente: Optional[str] = Field(default=None, nullable=True)
    instituicoes: Optional[str] = Field(default=None, nullable=True)  # Comma-separated or JSON
    
    # AI Metadata
    financiamento_mencionado: bool = Field(default=False, nullable=False)
    agencia_fomento: Optional[str] = Field(default=None, nullable=True)
    fonte_dado: FonteDado = Field(default=FonteDado.PDF_LATTES, nullable=False)
    confianca_ia: Optional[ConfiancaIA] = Field(default=None, nullable=True)
    trecho_original: Optional[str] = Field(default=None, nullable=True)
    status_validacao: StatusValidacao = Field(default=StatusValidacao.PENDENTE, index=True, nullable=False)

    # Relationships
    professor: Professor = Relationship(back_populates="projetos")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="projetos")
    financiamentos: List["Financiamento"] = Relationship(back_populates="projeto")
    anexos: List["Anexo"] = Relationship(back_populates="projeto")

class Evento(UUIDModel, TimestampModel, table=True):
    __tablename__ = "eventos"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    curriculo_upload_id: Optional[str] = Field(default=None, foreign_key="curriculo_uploads.id", index=True, nullable=True)

    nome_evento: str = Field(nullable=False, index=True)
    ano: Optional[int] = Field(default=None, index=True, nullable=True)
    cidade: Optional[str] = Field(default=None, nullable=True)
    pais: Optional[str] = Field(default=None, nullable=True)
    tipo_participacao: Optional[str] = Field(default=None, nullable=True)
    titulo_trabalho: Optional[str] = Field(default=None, nullable=True)
    eh_organizacao: bool = Field(default=False, index=True, nullable=False)
    escopo: Optional[EscopoEvento] = Field(default=None, nullable=True)
    instituicao_promotora: Optional[str] = Field(default=None, nullable=True)

    # AI Metadata
    financiamento_mencionado: bool = Field(default=False, nullable=False)
    fonte_financiamento: Optional[str] = Field(default=None, nullable=True)
    fonte_dado: FonteDado = Field(default=FonteDado.PDF_LATTES, nullable=False)
    confianca_ia: Optional[ConfiancaIA] = Field(default=None, nullable=True)
    trecho_original: Optional[str] = Field(default=None, nullable=True)
    status_validacao: StatusValidacao = Field(default=StatusValidacao.PENDENTE, index=True, nullable=False)

    # Relationships
    professor: Professor = Relationship(back_populates="eventos")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="eventos")
    financiamentos: List["Financiamento"] = Relationship(back_populates="evento")
    anexos: List["Anexo"] = Relationship(back_populates="evento")

class Producao(UUIDModel, TimestampModel, table=True):
    __tablename__ = "producoes"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    curriculo_upload_id: Optional[str] = Field(default=None, foreign_key="curriculo_uploads.id", index=True, nullable=True)

    tipo: str = Field(nullable=False, index=True) # artigo, livro, capitulo, anais, resumo, tecnica, outra
    titulo: str = Field(nullable=False, index=True)
    ano: Optional[int] = Field(default=None, index=True, nullable=True)
    veiculo: Optional[str] = Field(default=None, nullable=True)
    doi: Optional[str] = Field(default=None, index=True, nullable=True)
    isbn: Optional[str] = Field(default=None, nullable=True)
    issn: Optional[str] = Field(default=None, nullable=True)
    evento_relacionado: Optional[str] = Field(default=None, nullable=True)
    projeto_relacionado_id: Optional[str] = Field(default=None, nullable=True)
    autores: Optional[str] = Field(default=None, nullable=True)
    qualis: Optional[str] = Field(default=None, nullable=True, index=True)
    scholar_h5_index: Optional[int] = Field(default=None, nullable=True, index=True)
    scholar_h5_median: Optional[int] = Field(default=None, nullable=True)
    scholar_metrics_year: Optional[int] = Field(default=None, nullable=True)
    idioma: Optional[str] = Field(default=None, nullable=True)
    indexadores: Optional[str] = Field(default=None, nullable=True)
    volume: Optional[str] = Field(default=None, nullable=True)
    paginas: Optional[str] = Field(default=None, nullable=True)
    eh_primeiro_autor: Optional[bool] = Field(default=None, nullable=True)

    # AI Metadata
    fonte_dado: FonteDado = Field(default=FonteDado.PDF_LATTES, nullable=False)
    confianca_ia: Optional[ConfiancaIA] = Field(default=None, nullable=True)
    trecho_original: Optional[str] = Field(default=None, nullable=True)
    status_validacao: StatusValidacao = Field(default=StatusValidacao.PENDENTE, index=True, nullable=False)

    # Relationships
    professor: Professor = Relationship(back_populates="producoes")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="producoes")

class Financiamento(UUIDModel, TimestampModel, table=True):
    __tablename__ = "financiamentos"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    projeto_id: Optional[str] = Field(default=None, foreign_key="projetos.id", index=True, nullable=True)
    evento_id: Optional[str] = Field(default=None, foreign_key="eventos.id", index=True, nullable=True)

    tipo: TipoFinanciamento = Field(default=TipoFinanciamento.PESQUISA, index=True, nullable=False)
    fonte: Optional[str] = Field(default=None, nullable=True)
    agencia: Optional[str] = Field(default=None, nullable=True)
    edital: Optional[str] = Field(default=None, nullable=True)
    numero_processo: Optional[str] = Field(default=None, index=True, nullable=True)
    
    valor_solicitado: Optional[float] = Field(default=None, nullable=True)
    valor_aprovado: Optional[float] = Field(default=None, nullable=True)
    valor_executado: Optional[float] = Field(default=None, nullable=True)
    
    ano: Optional[int] = Field(default=None, index=True, nullable=True)
    vigencia_inicio: Optional[date] = Field(default=None, nullable=True)
    vigencia_fim: Optional[date] = Field(default=None, nullable=True)
    situacao: Optional[str] = Field(default=None, nullable=True)

    # AI Metadata
    fonte_dado: FonteDado = Field(default=FonteDado.PDF_LATTES, nullable=False)
    confianca: Optional[ConfiancaIA] = Field(default=None, nullable=True)
    trecho_original: Optional[str] = Field(default=None, nullable=True)
    status_validacao: StatusValidacao = Field(default=StatusValidacao.PENDENTE, index=True, nullable=False)

    # Relationships
    professor: Professor = Relationship(back_populates="financiamentos")
    projeto: Optional[Projeto] = Relationship(back_populates="financiamentos")
    evento: Optional[Evento] = Relationship(back_populates="financiamentos")
    anexos: List["Anexo"] = Relationship(back_populates="financiamento")

class RelatorioProjeto(UUIDModel, TimestampModel, table=True):
    __tablename__ = "relatorios_projeto"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    titulo: str = Field(nullable=False, index=True)
    tipo: TipoProjeto = Field(default=TipoProjeto.PESQUISA, index=True, nullable=False)
    linha_pesquisa_id: Optional[str] = Field(default=None, foreign_key="linhas_pesquisa.id", index=True, nullable=True)
    
    periodo_inicio: Optional[date] = Field(default=None, nullable=True)
    periodo_fim: Optional[date] = Field(default=None, nullable=True)
    situacao: Optional[str] = Field(default=None, nullable=True)
    resumo: Optional[str] = Field(default=None, nullable=True)
    participantes: Optional[str] = Field(default=None, nullable=True)
    alunos_envolvidos: Optional[str] = Field(default=None, nullable=True)
    instituicoes_parceiras: Optional[str] = Field(default=None, nullable=True)
    
    # Financial fields inside manual report
    houve_financiamento: bool = Field(default=False, nullable=False)
    fonte_financiamento: Optional[str] = Field(default=None, nullable=True)
    agencia: Optional[str] = Field(default=None, nullable=True)
    edital: Optional[str] = Field(default=None, nullable=True)
    numero_processo: Optional[str] = Field(default=None, nullable=True)
    tipo_recurso: Optional[TipoRecurso] = Field(default=None, nullable=True)
    
    valor_solicitado: Optional[float] = Field(default=None, nullable=True)
    valor_aprovado: Optional[float] = Field(default=None, nullable=True)
    valor_executado: Optional[float] = Field(default=None, nullable=True)
    
    vigencia_inicio: Optional[date] = Field(default=None, nullable=True)
    vigencia_fim: Optional[date] = Field(default=None, nullable=True)
    situacao_financeira: Optional[str] = Field(default=None, nullable=True)
    
    resultados: Optional[str] = Field(default=None, nullable=True)
    impacto_social: Optional[str] = Field(default=None, nullable=True)
    observacoes: Optional[str] = Field(default=None, nullable=True)

    tema_principal: Optional[str] = Field(default=None, nullable=True)
    publico_atendido: Optional[str] = Field(default=None, nullable=True)
    territorio_impactado: Optional[str] = Field(default=None, nullable=True)
    ods_relacionado: Optional[str] = Field(default=None, nullable=True)
    produto_gerado: Optional[str] = Field(default=None, nullable=True)
    tipo_impacto: Optional[TipoImpactoProjeto] = Field(default=None, nullable=True)
    possui_financiamento_confirmado: Optional[bool] = Field(default=None, nullable=True)

    # Relationships
    professor: Professor = Relationship(back_populates="relatorios_projeto")
    linha_pesquisa: Optional[LinhaPesquisa] = Relationship(back_populates="relatorios")
    anexos: List["Anexo"] = Relationship(back_populates="relatorio_projeto")

class Anexo(UUIDModel, table=True):
    __tablename__ = "anexos"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    relatorio_projeto_id: Optional[str] = Field(default=None, foreign_key="relatorios_projeto.id", index=True, nullable=True)
    financiamento_id: Optional[str] = Field(default=None, foreign_key="financiamentos.id", index=True, nullable=True)
    projeto_id: Optional[str] = Field(default=None, foreign_key="projetos.id", index=True, nullable=True)
    evento_id: Optional[str] = Field(default=None, foreign_key="eventos.id", index=True, nullable=True)

    tipo_anexo: str = Field(nullable=False) # edital, termo_de_concessao, etc.
    arquivo_url: str = Field(nullable=False)
    arquivo_nome: str = Field(nullable=False)
    descricao: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    professor: Professor = Relationship(back_populates="anexos")
    relatorio_projeto: Optional[RelatorioProjeto] = Relationship(back_populates="anexos")
    financiamento: Optional[Financiamento] = Relationship(back_populates="anexos")
    projeto: Optional[Projeto] = Relationship(back_populates="anexos")
    evento: Optional[Evento] = Relationship(back_populates="anexos")

class AlertaLacuna(UUIDModel, TimestampModel, table=True):
    __tablename__ = "alertas_lacunas"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    curriculo_upload_id: Optional[str] = Field(default=None, foreign_key="curriculo_uploads.id", index=True, nullable=True)

    tipo_lacuna: str = Field(nullable=False, index=True)
    descricao: str = Field(nullable=False)
    gravidade: GravidadeLacuna = Field(default=GravidadeLacuna.MEDIA, index=True, nullable=False)
    acao_recomendada: Optional[str] = Field(default=None, nullable=True)
    resolvido: bool = Field(default=False, index=True, nullable=False)

    secao_documento: Optional[str] = Field(default=None, nullable=True, index=True)
    entidade_relacionada: Optional[str] = Field(default=None, nullable=True)
    entidade_id: Optional[str] = Field(default=None, nullable=True, index=True)
    sugestao_de_correcao: Optional[str] = Field(default=None, nullable=True)
    prioridade: Optional[str] = Field(default=None, nullable=True)
    responsavel: Optional[str] = Field(default=None, nullable=True)
    prazo: Optional[date] = Field(default=None, nullable=True)
    status_tratamento: Optional[StatusTratamentoLacuna] = Field(
        default=StatusTratamentoLacuna.ABERTA,
        sa_column=Column(
            SAEnum(
                StatusTratamentoLacuna,
                values_callable=lambda obj: [e.value for e in obj],
                native_enum=False,
                length=32,
            ),
            nullable=True,
            index=True,
        ),
    )

    # Relationships
    professor: Professor = Relationship(back_populates="alertas_lacunas")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="alertas_lacunas")

class FormacaoAcademica(UUIDModel, TimestampModel, table=True):
    __tablename__ = "formacoes_academicas"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    curriculo_upload_id: Optional[str] = Field(
        default=None, foreign_key="curriculo_uploads.id", index=True, nullable=True
    )

    nivel: NivelFormacao = Field(default=NivelFormacao.OUTRA, index=True, nullable=False)
    curso: Optional[str] = Field(default=None, nullable=True)
    instituicao: Optional[str] = Field(default=None, nullable=True)
    ano_inicio: Optional[int] = Field(default=None, index=True, nullable=True)
    ano_fim: Optional[int] = Field(default=None, index=True, nullable=True)
    area_conhecimento: Optional[str] = Field(default=None, nullable=True)
    pais: Optional[str] = Field(default=None, nullable=True)
    periodo_sanduiche: bool = Field(default=False, nullable=False)
    instituicao_exterior: Optional[str] = Field(default=None, nullable=True)

    fonte_dado: FonteDado = Field(default=FonteDado.PDF_LATTES, nullable=False)
    confianca_ia: Optional[ConfiancaIA] = Field(default=None, nullable=True)
    trecho_original: Optional[str] = Field(default=None, nullable=True)
    status_validacao: StatusValidacao = Field(
        default=StatusValidacao.PENDENTE, index=True, nullable=False
    )

    professor: Professor = Relationship(back_populates="formacoes")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="formacoes")


class Orientacao(UUIDModel, TimestampModel, table=True):
    __tablename__ = "orientacoes"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    curriculo_upload_id: Optional[str] = Field(
        default=None, foreign_key="curriculo_uploads.id", index=True, nullable=True
    )

    tipo: TipoOrientacao = Field(default=TipoOrientacao.OUTRA, index=True, nullable=False)
    status: StatusOrientacao = Field(default=StatusOrientacao.CONCLUIDA, index=True, nullable=False)
    nome_orientando: Optional[str] = Field(default=None, nullable=True, index=True)
    titulo_trabalho: Optional[str] = Field(default=None, nullable=True)
    instituicao: Optional[str] = Field(default=None, nullable=True)
    ano_inicio: Optional[int] = Field(default=None, index=True, nullable=True)
    ano_conclusao: Optional[int] = Field(default=None, index=True, nullable=True)
    papel: PapelOrientacao = Field(default=PapelOrientacao.ORIENTADOR, nullable=False)

    fonte_dado: FonteDado = Field(default=FonteDado.PDF_LATTES, nullable=False)
    confianca_ia: Optional[ConfiancaIA] = Field(default=None, nullable=True)
    trecho_original: Optional[str] = Field(default=None, nullable=True)
    observacoes: Optional[str] = Field(default=None, nullable=True)
    status_validacao: StatusValidacao = Field(
        default=StatusValidacao.PENDENTE, index=True, nullable=False
    )

    professor: Professor = Relationship(back_populates="orientacoes")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="orientacoes")


class Banca(UUIDModel, TimestampModel, table=True):
    __tablename__ = "bancas"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    curriculo_upload_id: Optional[str] = Field(
        default=None, foreign_key="curriculo_uploads.id", index=True, nullable=True
    )

    tipo: TipoBanca = Field(default=TipoBanca.OUTRA, index=True, nullable=False)
    nivel: NivelBanca = Field(default=NivelBanca.OUTRO, index=True, nullable=False)
    nome_candidato: Optional[str] = Field(default=None, nullable=True, index=True)
    titulo_trabalho: Optional[str] = Field(default=None, nullable=True)
    instituicao: Optional[str] = Field(default=None, nullable=True)
    ano: Optional[int] = Field(default=None, index=True, nullable=True)
    papel: PapelBanca = Field(default=PapelBanca.MEMBRO, nullable=False)

    fonte_dado: FonteDado = Field(default=FonteDado.PDF_LATTES, nullable=False)
    confianca_ia: Optional[ConfiancaIA] = Field(default=None, nullable=True)
    trecho_original: Optional[str] = Field(default=None, nullable=True)
    observacoes: Optional[str] = Field(default=None, nullable=True)
    status_validacao: StatusValidacao = Field(
        default=StatusValidacao.PENDENTE, index=True, nullable=False
    )

    professor: Professor = Relationship(back_populates="bancas")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="bancas")


class ProducaoTecnica(UUIDModel, TimestampModel, table=True):
    __tablename__ = "producoes_tecnicas"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    curriculo_upload_id: Optional[str] = Field(
        default=None, foreign_key="curriculo_uploads.id", index=True, nullable=True
    )
    tipo: TipoProducaoTecnica = Field(default=TipoProducaoTecnica.OUTRA, index=True, nullable=False)
    titulo: str = Field(nullable=False, index=True)
    ano: Optional[int] = Field(default=None, index=True, nullable=True)
    instituicao: Optional[str] = Field(default=None, nullable=True)
    descricao: Optional[str] = Field(default=None, nullable=True)
    url: Optional[str] = Field(default=None, nullable=True)
    fonte_dado: FonteDado = Field(default=FonteDado.PDF_LATTES, nullable=False)
    confianca_ia: Optional[ConfiancaIA] = Field(default=None, nullable=True)
    trecho_original: Optional[str] = Field(default=None, nullable=True)
    status_validacao: StatusValidacao = Field(
        default=StatusValidacao.PENDENTE, index=True, nullable=False
    )
    professor: Professor = Relationship(back_populates="producoes_tecnicas")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="producoes_tecnicas")


class PremioTitulo(UUIDModel, TimestampModel, table=True):
    __tablename__ = "premios_titulos"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    curriculo_upload_id: Optional[str] = Field(
        default=None, foreign_key="curriculo_uploads.id", index=True, nullable=True
    )
    tipo: TipoPremio = Field(default=TipoPremio.OUTRO, index=True, nullable=False)
    nome: str = Field(nullable=False, index=True)
    ano: Optional[int] = Field(default=None, index=True, nullable=True)
    instituicao_concedente: Optional[str] = Field(default=None, nullable=True)
    descricao: Optional[str] = Field(default=None, nullable=True)
    fonte_dado: FonteDado = Field(default=FonteDado.PDF_LATTES, nullable=False)
    confianca_ia: Optional[ConfiancaIA] = Field(default=None, nullable=True)
    trecho_original: Optional[str] = Field(default=None, nullable=True)
    status_validacao: StatusValidacao = Field(
        default=StatusValidacao.PENDENTE, index=True, nullable=False
    )
    professor: Professor = Relationship(back_populates="premios")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="premios")


class GrupoPesquisaDocente(UUIDModel, TimestampModel, table=True):
    __tablename__ = "grupos_pesquisa_docente"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    curriculo_upload_id: Optional[str] = Field(
        default=None, foreign_key="curriculo_uploads.id", index=True, nullable=True
    )
    nome_grupo: str = Field(nullable=False, index=True)
    codigo_dgp: Optional[str] = Field(default=None, nullable=True)
    papel: PapelGrupoPesquisa = Field(default=PapelGrupoPesquisa.MEMBRO, nullable=False)
    linha_tematica: Optional[str] = Field(default=None, nullable=True)
    instituicao: Optional[str] = Field(default=None, nullable=True)
    fonte_dado: FonteDado = Field(default=FonteDado.PDF_LATTES, nullable=False)
    confianca_ia: Optional[ConfiancaIA] = Field(default=None, nullable=True)
    trecho_original: Optional[str] = Field(default=None, nullable=True)
    status_validacao: StatusValidacao = Field(
        default=StatusValidacao.PENDENTE, index=True, nullable=False
    )
    professor: Professor = Relationship(back_populates="grupos_pesquisa")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="grupos_pesquisa")


class PerfilLattes(UUIDModel, TimestampModel, table=True):
    __tablename__ = "perfis_lattes"

    professor_id: str = Field(foreign_key="professores.id", index=True, nullable=False)
    curriculo_upload_id: Optional[str] = Field(
        default=None, foreign_key="curriculo_uploads.id", index=True, nullable=True
    )

    data_ultima_atualizacao: Optional[date] = Field(default=None, nullable=True)
    resumo_cv: Optional[str] = Field(default=None, nullable=True)
    palavras_chave: Optional[str] = Field(default=None, nullable=True)
    nome_citacao: Optional[str] = Field(default=None, nullable=True)
    link_orcid: Optional[str] = Field(default=None, nullable=True)

    fonte_dado: FonteDado = Field(default=FonteDado.PDF_LATTES, nullable=False)
    confianca_ia: Optional[ConfiancaIA] = Field(default=None, nullable=True)
    trecho_original: Optional[str] = Field(default=None, nullable=True)
    status_validacao: StatusValidacao = Field(
        default=StatusValidacao.PENDENTE, index=True, nullable=False
    )

    professor: Professor = Relationship(back_populates="perfis_lattes")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="perfis_lattes")


class EventoInstitucional(UUIDModel, TimestampModel, table=True):
    __tablename__ = "eventos_institucionais"

    nome: str = Field(nullable=False, index=True)
    edicao: Optional[str] = Field(default=None, nullable=True)
    ano: Optional[int] = Field(default=None, index=True, nullable=True)
    tema: Optional[str] = Field(default=None, nullable=True)
    data_inicio: Optional[date] = Field(default=None, nullable=True)
    data_fim: Optional[date] = Field(default=None, nullable=True)
    local: Optional[str] = Field(default=None, nullable=True)
    abrangencia: Optional[str] = Field(default=None, nullable=True)
    numero_inscritos: Optional[int] = Field(default=None, nullable=True)
    numero_trabalhos: Optional[int] = Field(default=None, nullable=True)
    numero_convidados: Optional[int] = Field(default=None, nullable=True)
    agencias_financiadoras: Optional[str] = Field(default=None, nullable=True)
    valor_aprovado: Optional[float] = Field(default=None, nullable=True)
    valor_executado: Optional[float] = Field(default=None, nullable=True)
    descricao: Optional[str] = Field(default=None, nullable=True)


class Egresso(UUIDModel, TimestampModel, table=True):
    __tablename__ = "egressos"

    nome: str = Field(nullable=False, index=True)
    ano_ingresso: Optional[int] = Field(default=None, nullable=True)
    ano_conclusao: Optional[int] = Field(default=None, index=True, nullable=True)
    cidade_origem: Optional[str] = Field(default=None, nullable=True)
    estado_origem: Optional[str] = Field(default=None, nullable=True)
    genero: Optional[str] = Field(default=None, nullable=True)
    raca_cor: Optional[str] = Field(default=None, nullable=True)
    escola_origem: Optional[str] = Field(default=None, nullable=True)
    ingresso_por_cota: bool = Field(default=False, nullable=False)
    atividade_atual: Optional[str] = Field(default=None, nullable=True)
    instituicao_atual: Optional[str] = Field(default=None, nullable=True)
    cidade_atuacao: Optional[str] = Field(default=None, nullable=True)
    estado_atuacao: Optional[str] = Field(default=None, nullable=True)
    setor_atuacao: Optional[str] = Field(default=None, nullable=True)
    esta_em_doutorado: bool = Field(default=False, nullable=False)
    instituicao_doutorado: Optional[str] = Field(default=None, nullable=True)
    impacto_social_resumo: Optional[str] = Field(default=None, nullable=True)


class ProcessoSeletivo(UUIDModel, TimestampModel, table=True):
    __tablename__ = "processos_seletivos"

    ano: int = Field(index=True, nullable=False)
    nivel: str = Field(nullable=False, index=True)
    vagas: int = Field(nullable=False)
    inscritos: int = Field(nullable=False)
    inscricoes_deferidas: Optional[int] = Field(default=None, nullable=True)
    aprovados: Optional[int] = Field(default=None, nullable=True)
    matriculados: Optional[int] = Field(default=None, nullable=True)
    cotistas: Optional[int] = Field(default=None, nullable=True)
    observacoes: Optional[str] = Field(default=None, nullable=True)


class LogValidacao(UUIDModel, table=True):
    __tablename__ = "logs_validacao"

    user_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    entidade: str = Field(nullable=False, index=True) # projetos, eventos, etc.
    entidade_id: str = Field(index=True, nullable=False)
    acao: str = Field(nullable=False) # confirmar, editar, descartar
    valor_anterior: Optional[str] = Field(default=None, nullable=True) # JSON or simple string
    valor_novo: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
