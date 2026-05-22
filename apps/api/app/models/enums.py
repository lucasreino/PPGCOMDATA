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
    XML_LATTES = "xml_lattes"
    RELATORIO_MANUAL = "relatorio_manual"
    ANEXO = "anexo"
    EDICAO_COORDENACAO = "edicao_coordenacao"

class NivelFormacao(str, Enum):
    GRADUACAO = "graduacao"
    ESPECIALIZACAO = "especializacao"
    MESTRADO = "mestrado"
    DOUTORADO = "doutorado"
    POS_DOUTORADO = "pos_doutorado"
    OUTRA = "outra"

class TipoOrientacao(str, Enum):
    MESTRADO = "mestrado"
    DOUTORADO = "doutorado"
    IC = "ic"
    TCC = "tcc"
    POS_DOUTORADO = "pos_doutorado"
    OUTRA = "outra"

class StatusOrientacao(str, Enum):
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"

class PapelOrientacao(str, Enum):
    ORIENTADOR = "orientador"
    COORIENTADOR = "coorientador"

class TipoBanca(str, Enum):
    QUALIFICACAO = "qualificacao"
    DEFESA = "defesa"
    EXAME = "exame"
    OUTRA = "outra"

class NivelBanca(str, Enum):
    MESTRADO = "mestrado"
    DOUTORADO = "doutorado"
    OUTRO = "outro"

class PapelBanca(str, Enum):
    PRESIDENTE = "presidente"
    MEMBRO = "membro"
    SUPLENTE = "suplente"
    OUTRO = "outro"

class EscopoEvento(str, Enum):
    NACIONAL = "nacional"
    INTERNACIONAL = "internacional"
    OUTRO = "outro"

class TipoProducaoTecnica(str, Enum):
    AUDIOVISUAL = "audiovisual"
    SOFTWARE = "software"
    MATERIAL_DIDATICO = "material_didatico"
    TRADUCAO = "traducao"
    PATENTE = "patente"
    OUTRA = "outra"

class TipoPremio(str, Enum):
    PREMIO = "premio"
    BOLSA_PRODUTIVIDADE = "bolsa_produtividade"
    TITULO_HONORIFICO = "titulo_honorifico"
    OUTRO = "outro"

class PapelGrupoPesquisa(str, Enum):
    LIDER = "lider"
    VICE_LIDER = "vice_lider"
    MEMBRO = "membro"
    OUTRO = "outro"

class StatusTratamentoLacuna(str, Enum):
    ABERTA = "aberta"
    EM_ANALISE = "em_analise"
    RESOLVIDA = "resolvida"

class TipoImpactoProjeto(str, Enum):
    LOCAL = "local"
    REGIONAL = "regional"
    NACIONAL = "nacional"
    INTERNACIONAL = "internacional"
