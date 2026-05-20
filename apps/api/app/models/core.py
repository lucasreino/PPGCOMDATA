from datetime import date
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import UUIDModel, TimestampModel
from app.models.enums import UserRole, TipoDocente

if TYPE_CHECKING:
    from app.models.data import (
        CurriculoUpload, PdfPage, PdfSection, Projeto, Evento, 
        Producao, Financiamento, RelatorioProjeto, Anexo, AlertaLacuna
    )

class User(UUIDModel, TimestampModel, table=True):
    __tablename__ = "users"

    name: str = Field(nullable=False)
    email: str = Field(unique=True, index=True, nullable=False)
    role: UserRole = Field(default=UserRole.SECRETARIA, nullable=False)
    password_hash: str = Field(nullable=False)

class LinhaPesquisa(UUIDModel, TimestampModel, table=True):
    __tablename__ = "linhas_pesquisa"

    nome: str = Field(nullable=False, index=True)
    descricao: Optional[str] = Field(default=None, nullable=True)
    status: bool = Field(default=True, nullable=False)

    # Relationships
    professores: List["Professor"] = Relationship(back_populates="linha_pesquisa")
    relatorios: List["RelatorioProjeto"] = Relationship(back_populates="linha_pesquisa")

class Professor(UUIDModel, TimestampModel, table=True):
    __tablename__ = "professores"

    nome_completo: str = Field(nullable=False, index=True)
    nome_citacao: Optional[str] = Field(default=None, nullable=True)
    email: Optional[str] = Field(default=None, nullable=True, index=True)
    link_lattes: Optional[str] = Field(default=None, nullable=True)
    id_lattes: Optional[str] = Field(default=None, nullable=True, index=True)
    tipo_docente: TipoDocente = Field(default=TipoDocente.PERMANENTE, nullable=False, index=True)
    data_entrada_programa: Optional[date] = Field(default=None, nullable=True)
    status: bool = Field(default=True, nullable=False)
    observacoes: Optional[str] = Field(default=None, nullable=True)
    
    # Foreign Keys
    linha_pesquisa_id: Optional[str] = Field(
        default=None, 
        foreign_key="linhas_pesquisa.id",
        nullable=True,
        index=True
    )

    # Relationships
    linha_pesquisa: Optional[LinhaPesquisa] = Relationship(back_populates="professores")
    uploads: List["CurriculoUpload"] = Relationship(back_populates="professor")
    pdf_pages: List["PdfPage"] = Relationship(back_populates="professor")
    pdf_sections: List["PdfSection"] = Relationship(back_populates="professor")
    projetos: List["Projeto"] = Relationship(back_populates="professor")
    eventos: List["Evento"] = Relationship(back_populates="professor")
    producoes: List["Producao"] = Relationship(back_populates="professor")
    financiamentos: List["Financiamento"] = Relationship(back_populates="professor")
    relatorios_projeto: List["RelatorioProjeto"] = Relationship(back_populates="professor")
    anexos: List["Anexo"] = Relationship(back_populates="professor")
    alertas_lacunas: List["AlertaLacuna"] = Relationship(back_populates="professor")
