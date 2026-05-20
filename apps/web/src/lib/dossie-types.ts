export interface DossieFilters {
  professor_id?: string;
  linha_pesquisa_id?: string;
  ano_inicio?: number;
  ano_fim?: number;
  apenas_validados?: boolean;
}

export interface DossieOverview {
  total_docentes: number;
  total_producoes: number;
  total_projetos: number;
  total_eventos: number;
  total_financiamentos: number;
  total_lacunas: number;
  lacunas_pendentes: number;
  fomento_total: { solicitado: number; aprovado: number; executado: number };
  validacao_pendentes: number;
  total_orientacoes: number;
  orientacoes_concluidas?: number;
  modulos_disponiveis: Record<string, boolean>;
}

export interface DossieProducao {
  totais: Record<string, number>;
  producao_por_tipo: Record<string, number>;
  producao_por_ano: Record<string, number>;
  producao_por_docente: Record<string, number>;
  producao_por_linha: Record<string, number>;
  tabela_por_docente: Array<Record<string, string | number>>;
}

export interface DossieFinanciamento {
  total_financiamentos_mencionados: number;
  total_financiamentos_confirmados: number;
  valor_total_aprovado: number;
  valor_total_executado: number;
  financiamentos_por_agencia: Record<string, number>;
  financiamentos_por_ano: Record<string, number>;
  comparativo: { mencionados: number; confirmados: number };
  matriz_fomento: Array<Record<string, unknown>>;
}

export interface DossieLacunas {
  total_lacunas: number;
  lacunas_abertas: number;
  lacunas_criticas: number;
  lacunas_resolvidas: number;
  lacunas_por_tipo: Record<string, number>;
  lacunas_por_gravidade: Record<string, number>;
  lacunas_por_docente: Record<string, number>;
  tabela: Array<Record<string, unknown>>;
}
