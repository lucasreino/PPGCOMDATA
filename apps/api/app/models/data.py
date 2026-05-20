from datetime import datetime, date
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel
from app.models.base import UUIDModel, TimestampModel
from app.models.enums import (
    StatusProcessamento, StatusValidacao, TipoProjeto, TipoFinanciamento,
    ConfiancaIA, GravidadeLacuna, TipoRecurso, FonteDado
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

    # Relationships
    professor: Professor = Relationship(back_populates="alertas_lacunas")
    upload: Optional[CurriculoUpload] = Relationship(back_populates="alertas_lacunas")

class LogValidacao(UUIDModel, table=True):
    __tablename__ = "logs_validacao"

    user_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    entidade: str = Field(nullable=False, index=True) # projetos, eventos, etc.
    entidade_id: str = Field(index=True, nullable=False)
    acao: str = Field(nullable=False) # confirmar, editar, descartar
    valor_anterior: Optional[str] = Field(default=None, nullable=True) # JSON or simple string
    valor_novo: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
