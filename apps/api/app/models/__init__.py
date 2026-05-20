from app.models.enums import (
    UserRole, TipoDocente, StatusProcessamento, StatusValidacao,
    TipoProjeto, TipoFinanciamento, ConfiancaIA, GravidadeLacuna,
    TipoRecurso, FonteDado, NivelFormacao, TipoOrientacao, StatusOrientacao,
    PapelOrientacao, TipoBanca, NivelBanca, PapelBanca,
)
from app.models.core import User, LinhaPesquisa, Professor
from app.models.data import (
    CurriculoUpload, PdfPage, PdfSection, Projeto, Evento,
    Producao, Financiamento, RelatorioProjeto, Anexo, AlertaLacuna, LogValidacao,
    FormacaoAcademica, Orientacao, Banca, PerfilLattes,
    ProducaoTecnica, PremioTitulo, GrupoPesquisaDocente,
)
