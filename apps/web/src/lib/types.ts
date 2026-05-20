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
export type EntityTab = "projetos" | "eventos" | "producoes" | "financiamentos";
