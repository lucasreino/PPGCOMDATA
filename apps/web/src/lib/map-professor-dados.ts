import type {
  Evento,
  Financiamento,
  FormacaoAcademica,
  GrupoPesquisa,
  Orientacao,
  Premio,
  Producao,
  ProducaoTecnica,
  Projeto,
  ProfessorResumo,
} from "@/lib/types";

type Conf = "alta" | "media" | "baixa";
type Val = "pendente" | "confirmado" | "editado" | "descartado";

function conf(v: unknown): Conf {
  return v === "alta" || v === "media" || v === "baixa" ? v : "media";
}

function val(v: unknown): Val {
  const s = String(v || "pendente");
  if (s === "confirmado" || s === "editado" || s === "descartado") return s;
  return "pendente";
}

export function mapProjeto(r: Record<string, unknown>): Projeto {
  return {
    id: String(r.id),
    titulo: String(r.titulo || ""),
    tipo: String(r.tipo || ""),
    situacao: String(r.situacao || ""),
    ano_inicio: Number(r.ano_inicio) || 0,
    ano_fim: r.ano_fim != null ? Number(r.ano_fim) : null,
    descricao: String(r.descricao || ""),
    papel_docente: String(r.papel_docente || ""),
    instituicoes: String(r.instituicoes || ""),
    financiamento_mencionado: Boolean(r.financiamento_mencionado),
    agencia_fomento: r.agencia_fomento != null ? String(r.agencia_fomento) : null,
    confianca_ia: conf(r.confianca_ia),
    trecho_original: String(r.trecho_original || ""),
    status_validacao: val(r.status_validacao),
  };
}

export function mapEvento(r: Record<string, unknown>): Evento {
  return {
    id: String(r.id),
    nome_evento: String(r.nome_evento || ""),
    ano: Number(r.ano) || 0,
    cidade: String(r.cidade || ""),
    pais: String(r.pais || ""),
    tipo_participacao: String(r.tipo_participacao || ""),
    titulo_trabalho: String(r.titulo_trabalho || ""),
    eh_organizacao: Boolean(r.eh_organizacao),
    financiamento_mencionado: Boolean(r.financiamento_mencionado),
    fonte_financiamento:
      r.fonte_financiamento != null ? String(r.fonte_financiamento) : null,
    confianca_ia: conf(r.confianca_ia),
    trecho_original: String(r.trecho_original || ""),
    status_validacao: val(r.status_validacao),
  };
}

export function mapProducao(r: Record<string, unknown>): Producao {
  return {
    id: String(r.id),
    tipo: String(r.tipo || ""),
    titulo: String(r.titulo || ""),
    ano: Number(r.ano) || 0,
    veiculo: String(r.veiculo || ""),
    doi: r.doi != null ? String(r.doi) : null,
    issn: r.issn != null ? String(r.issn) : null,
    qualis: r.qualis != null ? String(r.qualis) : null,
    confianca_ia: conf(r.confianca_ia),
    trecho_original: String(r.trecho_original || ""),
    status_validacao: val(r.status_validacao),
  };
}

export function mapFinanciamento(r: Record<string, unknown>): Financiamento {
  return {
    id: String(r.id),
    tipo: String(r.tipo || ""),
    fonte: String(r.fonte || ""),
    agencia: String(r.agencia || ""),
    edital: r.edital != null ? String(r.edital) : null,
    numero_processo:
      r.numero_processo != null ? String(r.numero_processo) : null,
    valor: String(r.valor || ""),
    ano: Number(r.ano) || 0,
    confianca: conf(r.confianca),
    trecho_original: String(r.trecho_original || ""),
    status_validacao: val(r.status_validacao),
  };
}

export function mapOrientacao(r: Record<string, unknown>): Orientacao {
  return {
    id: String(r.id),
    tipo: String(r.tipo || "outra"),
    status: String(r.status || ""),
    nome_orientando: r.nome_orientando != null ? String(r.nome_orientando) : null,
    titulo_trabalho:
      r.titulo_trabalho != null ? String(r.titulo_trabalho) : null,
    instituicao: r.instituicao != null ? String(r.instituicao) : null,
    ano_inicio: r.ano_inicio != null ? Number(r.ano_inicio) : null,
    ano_conclusao: r.ano_conclusao != null ? Number(r.ano_conclusao) : null,
    papel: String(r.papel || "orientador"),
    confianca_ia: conf(r.confianca_ia),
    trecho_original: String(r.trecho_original || ""),
    status_validacao: val(r.status_validacao),
  };
}

export function mapFormacao(r: Record<string, unknown>): FormacaoAcademica {
  return {
    id: String(r.id),
    nivel: String(r.nivel || ""),
    curso: r.curso != null ? String(r.curso) : null,
    instituicao: r.instituicao != null ? String(r.instituicao) : null,
    ano_inicio: r.ano_inicio != null ? Number(r.ano_inicio) : null,
    ano_fim: r.ano_fim != null ? Number(r.ano_fim) : null,
    area_conhecimento:
      r.area_conhecimento != null ? String(r.area_conhecimento) : null,
    periodo_sanduiche: Boolean(r.periodo_sanduiche),
    confianca_ia: conf(r.confianca_ia),
    trecho_original: String(r.trecho_original || ""),
    status_validacao: val(r.status_validacao),
  };
}

export function mapProducaoTecnica(r: Record<string, unknown>): ProducaoTecnica {
  return {
    id: String(r.id),
    tipo: String(r.tipo || ""),
    titulo: String(r.titulo || ""),
    ano: r.ano != null ? Number(r.ano) : null,
    instituicao: r.instituicao != null ? String(r.instituicao) : null,
    descricao: r.descricao != null ? String(r.descricao) : null,
    url: r.url != null ? String(r.url) : null,
    confianca_ia: conf(r.confianca_ia),
    trecho_original: String(r.trecho_original || ""),
    status_validacao: val(r.status_validacao),
  };
}

export function mapPremio(r: Record<string, unknown>): Premio {
  return {
    id: String(r.id),
    tipo: String(r.tipo || ""),
    nome: String(r.nome || ""),
    ano: r.ano != null ? Number(r.ano) : null,
    instituicao_concedente:
      r.instituicao_concedente != null ? String(r.instituicao_concedente) : null,
    descricao: r.descricao != null ? String(r.descricao) : null,
    confianca_ia: conf(r.confianca_ia),
    trecho_original: String(r.trecho_original || ""),
    status_validacao: val(r.status_validacao),
  };
}

export function mapGrupo(r: Record<string, unknown>): GrupoPesquisa {
  return {
    id: String(r.id),
    nome_grupo: String(r.nome_grupo || ""),
    codigo_dgp: r.codigo_dgp != null ? String(r.codigo_dgp) : null,
    papel: String(r.papel || ""),
    linha_tematica: r.linha_tematica != null ? String(r.linha_tematica) : null,
    instituicao: r.instituicao != null ? String(r.instituicao) : null,
    confianca_ia: conf(r.confianca_ia),
    trecho_original: String(r.trecho_original || ""),
    status_validacao: val(r.status_validacao),
  };
}

export interface BancaItem {
  id: string;
  tipo: string;
  nome_candidato: string | null;
  titulo_trabalho: string | null;
  ano: number | null;
  instituicao: string | null;
  status_validacao: Val;
}

export function mapBanca(r: Record<string, unknown>): BancaItem {
  return {
    id: String(r.id),
    tipo: String(r.tipo || ""),
    nome_candidato:
      r.nome_candidato != null ? String(r.nome_candidato) : null,
    titulo_trabalho:
      r.titulo_trabalho != null ? String(r.titulo_trabalho) : null,
    ano: r.ano != null ? Number(r.ano) : null,
    instituicao: r.instituicao != null ? String(r.instituicao) : null,
    status_validacao: val(r.status_validacao),
  };
}

export interface ProfessorDadosPayload {
  projetos: Projeto[];
  eventos: Evento[];
  producoes: Producao[];
  financiamentos: Financiamento[];
  orientacoes: Orientacao[];
  formacoes_academicas: FormacaoAcademica[];
  bancas: BancaItem[];
  producoes_tecnicas: ProducaoTecnica[];
  premios: Premio[];
  grupos_pesquisa: GrupoPesquisa[];
}

export function mapProfessorDados(raw: Record<string, unknown>): ProfessorDadosPayload {
  const arr = (key: string) =>
    (Array.isArray(raw[key]) ? raw[key] : []) as Record<string, unknown>[];

  return {
    projetos: arr("projetos").map(mapProjeto),
    eventos: arr("eventos").map(mapEvento),
    producoes: arr("producoes").map(mapProducao),
    financiamentos: arr("financiamentos").map(mapFinanciamento),
    orientacoes: arr("orientacoes").map(mapOrientacao),
    formacoes_academicas: arr("formacoes_academicas").map(mapFormacao),
    bancas: arr("bancas").map(mapBanca),
    producoes_tecnicas: arr("producoes_tecnicas").map(mapProducaoTecnica),
    premios: arr("premios").map(mapPremio),
    grupos_pesquisa: arr("grupos_pesquisa").map(mapGrupo),
  };
}

export function resumoFromApi(raw: Record<string, unknown>): ProfessorResumo {
  return {
    titulacao_maxima:
      raw.titulacao_maxima != null ? String(raw.titulacao_maxima) : null,
    data_ultima_atualizacao_lattes:
      raw.data_ultima_atualizacao_lattes != null
        ? String(raw.data_ultima_atualizacao_lattes)
        : null,
    total_orientacoes: Number(raw.total_orientacoes) || 0,
    orientacoes_concluidas: Number(raw.orientacoes_concluidas) || 0,
    orientacoes_em_andamento: Number(raw.orientacoes_em_andamento) || 0,
    orientacoes_ultimos_5_anos: Number(raw.orientacoes_ultimos_5_anos) || 0,
    total_bancas: Number(raw.total_bancas) || 0,
    total_formacoes: Number(raw.total_formacoes) || 0,
  };
}
