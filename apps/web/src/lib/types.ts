export interface Professor {
  id: string;
  nome_completo: string;
  linha: string;
  tipo: string;
  status: "pendente" | "processado" | "validado";
  ultimo_upload?: string;
}

export interface Projeto {
  id: string;
  titulo: string;
  tipo: string;
  situacao: string;
  ano_inicio: number;
  ano_fim: number | null;
  descricao: string;
  papel_docente: string;
  instituicoes: string;
  financiamento_mencionado: boolean;
  agencia_fomento: string | null;
  confianca_ia: "alta" | "media" | "baixa";
  trecho_original: string;
  status_validacao: "pendente" | "confirmado" | "editado" | "descartado";
}

export interface Evento {
  id: string;
  nome_evento: string;
  ano: number;
  cidade: string;
  pais: string;
  tipo_participacao: string;
  titulo_trabalho: string;
  eh_organizacao?: boolean;
  escopo?: string | null;
  financiamento_mencionado: boolean;
  fonte_financiamento: string | null;
  confianca_ia: "alta" | "media" | "baixa";
  trecho_original: string;
  status_validacao: "pendente" | "confirmado" | "editado" | "descartado";
}

export interface Producao {
  id: string;
  tipo: string;
  titulo: string;
  ano: number;
  veiculo: string;
  doi: string | null;
  issn: string | null;
  qualis?: string | null;
  autores?: string | null;
  idioma?: string | null;
  volume?: string | null;
  paginas?: string | null;
  confianca_ia: "alta" | "media" | "baixa";
  trecho_original: string;
  status_validacao: "pendente" | "confirmado" | "editado" | "descartado";
}

export interface Financiamento {
  id: string;
  tipo: string;
  fonte: string;
  agencia: string;
  edital: string | null;
  numero_processo: string | null;
  valor: string;
  ano: number;
  confianca: "alta" | "media" | "baixa";
  trecho_original: string;
  status_validacao: "pendente" | "confirmado" | "editado" | "descartado";
}

export interface Orientacao {
  id: string;
  tipo: string;
  status: string;
  nome_orientando: string | null;
  titulo_trabalho: string | null;
  instituicao: string | null;
  ano_inicio: number | null;
  ano_conclusao: number | null;
  papel: string;
  confianca_ia: "alta" | "media" | "baixa";
  trecho_original: string;
  status_validacao: "pendente" | "confirmado" | "editado" | "descartado";
}

export interface FormacaoAcademica {
  id: string;
  nivel: string;
  curso: string | null;
  instituicao: string | null;
  ano_inicio: number | null;
  ano_fim: number | null;
  area_conhecimento: string | null;
  periodo_sanduiche: boolean;
  confianca_ia: "alta" | "media" | "baixa";
  trecho_original: string;
  status_validacao: "pendente" | "confirmado" | "editado" | "descartado";
}

export interface ProfessorResumo {
  titulacao_maxima?: string | null;
  data_ultima_atualizacao_lattes?: string | null;
  total_orientacoes: number;
  orientacoes_concluidas: number;
  orientacoes_em_andamento: number;
  orientacoes_ultimos_5_anos: number;
  total_bancas: number;
  total_formacoes: number;
}

export interface AlertaLacuna {
  id: string;
  tipo_lacuna: string;
  descricao: string;
  gravidade: "alta" | "media" | "baixa";
  acao_recomendada: string;
  resolvido: boolean;
}

export interface LogAudit {
  id: string;
  acao: string;
  mensagem: string;
  timestamp: string;
}

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: string;
}

export type MainTab = "validacao" | "estatisticas" | "relatorios";
export type EntityTab =
  | "projetos"
  | "eventos"
  | "producoes"
  | "financiamentos"
  | "orientacoes"
  | "formacoes_academicas";

export type ValidationEntityType = EntityTab;
