from enum import Enum

class UserRole(str, Enum):
    ADMINISTRADOR = "administrador"
    COORDENACAO = "coordenacao"
    SECRETARIA = "secretaria"
    PROFESSOR = "professor"

class TipoDocente(str, Enum):
    PERMANENTE = "permanente"
    COLABORADOR = "colaborador"
    VISITANTE = "visitante"
    EXTERNO = "externo"

class StatusProcessamento(str, Enum):
    AGUARDANDO_PROCESSAMENTO = "aguardando_processamento"
    PROCESSANDO = "processando"
    PROCESSADO_COM_SUCESSO = "processado_com_sucesso"
    PROCESSADO_COM_ALERTAS = "processado_com_alertas"
    ERRO_NO_PROCESSAMENTO = "erro_no_processamento"
    AGUARDANDO_VALIDACAO = "aguardando_validacao"
    VALIDADO = "validado"

class StatusValidacao(str, Enum):
    PENDENTE = "pendente"
    CONFIRMADO = "confirmado"
    EDITADO = "editado"
    DESCARTADO = "descartado"
    INCOMPLETO = "incompleto"

class TipoProjeto(str, Enum):
    PESQUISA = "pesquisa"
    EXTENSAO = "extensao"
    DESENVOLVIMENTO = "desenvolvimento"
    ENSINO = "ensino"
    INOVACAO = "inovacao"
    OUTRO = "outro"

class TipoFinanciamento(str, Enum):
    PESQUISA = "pesquisa"
    EXTENSAO = "extensao"
    EVENTO = "evento"
    BOLSA = "bolsa"
    AUXILIO = "auxilio"
    DIARIA = "diaria"
    PASSAGEM = "passagem"
    TAXA_INSCRICAO = "taxa_inscricao"
    EQUIPAMENTO = "equipamento"
    MATERIAL_CONSUMO = "material_consumo"
    SERVICO_TERCEIROS = "servico_terceiros"
    PUBLICACAO = "publicacao"
    OUTRO = "outro"

class ConfiancaIA(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"

class GravidadeLacuna(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"

class TipoRecurso(str, Enum):
    BOLSA = "bolsa"
    AUXILIO_PESQUISA = "auxilio_pesquisa"
    AUXILIO_EXTENSAO = "auxilio_extensao"
    DIARIA = "diaria"
    PASSAGEM = "passagem"
    TAXA_INSCRICAO = "taxa_inscricao"
    EQUIPAMENTO = "equipamento"
    MATERIAL_CONSUMO = "material_consumo"
    SERVICO_TERCEIROS = "servico_terceiros"
    PUBLICACAO = "publicacao"
    OUTRO = "outro"

class FonteDado(str, Enum):
    PDF_LATTES = "pdf_lattes"
    RELATORIO_MANUAL = "relatorio_manual"
    ANEXO = "anexo"
    EDICAO_COORDENACAO = "edicao_coordenacao"
