export type KpiDetailColumn = {
  key: string;
  label: string;
  align?: "left" | "right" | "center";
  mono?: boolean;
  truncate?: boolean;
  format?: (value: unknown, row: Record<string, unknown>) => string;
};

export type KpiDetailState = {
  title: string;
  subtitle?: string;
  columns: KpiDetailColumn[];
  rows: Record<string, unknown>[];
  emptyMessage?: string;
};

export type DossieDataContext = {
  corpo: Record<string, unknown> | null;
  producao: Record<string, unknown> | null;
  projetos: Record<string, unknown> | null;
  financiamento: Record<string, unknown> | null;
  eventos: Record<string, unknown> | null;
  lacunas: Record<string, unknown> | null;
  egressos: Record<string, unknown> | null;
  demanda: Record<string, unknown> | null;
};

export const EMPTY_DOSSIE_CTX: DossieDataContext = {
  corpo: null,
  producao: null,
  projetos: null,
  financiamento: null,
  eventos: null,
  lacunas: null,
  egressos: null,
  demanda: null,
};

function rows<T extends Record<string, unknown>>(arr: unknown): T[] {
  return Array.isArray(arr) ? (arr as T[]) : [];
}

function str(v: unknown, fallback = "—"): string {
  if (v == null || v === "") return fallback;
  return String(v);
}

function boolSim(v: unknown): string {
  return v ? "Sim" : "Não";
}

const COL_DOCENTE_LINHA: KpiDetailColumn[] = [
  { key: "nome", label: "Docente" },
  { key: "linha", label: "Linha" },
  { key: "producoes", label: "Prod.", align: "right" },
  { key: "projetos", label: "Proj.", align: "right" },
  { key: "lacunas_abertas", label: "Lacunas", align: "right" },
];

const COL_PROJETO: KpiDetailColumn[] = [
  { key: "titulo", label: "Título", truncate: true },
  { key: "docente", label: "Docente" },
  { key: "tipo", label: "Tipo" },
  { key: "ano", label: "Ano", align: "center" },
  { key: "financiamento", label: "Financ.", align: "center" },
];

const COL_RELATORIO: KpiDetailColumn[] = [
  { key: "titulo", label: "Título", truncate: true },
  { key: "docente", label: "Docente" },
  { key: "tema", label: "Tema" },
  { key: "territorio", label: "Território" },
  { key: "tipo_impacto", label: "Impacto" },
];

const COL_FOMENTO: KpiDetailColumn[] = [
  { key: "agencia", label: "Agência" },
  { key: "ano", label: "Ano", align: "center" },
  { key: "docente", label: "Docente" },
  { key: "vinculo", label: "Vínculo", truncate: true },
  { key: "origem", label: "Origem", align: "center", mono: true },
  {
    key: "valor_aprovado",
    label: "Aprovado",
    align: "right",
    format: (v) => (v != null && v !== "" ? fmtBrl(Number(v)) : "—"),
  },
];

const COL_EVENTO_LATTES: KpiDetailColumn[] = [
  { key: "evento", label: "Evento", truncate: true },
  { key: "docente", label: "Docente" },
  { key: "ano", label: "Ano", align: "center" },
  { key: "cidade", label: "Cidade" },
  { key: "organizacao", label: "Org.", align: "center", format: boolSim },
];

const COL_EVENTO_INST: KpiDetailColumn[] = [
  { key: "nome", label: "Evento", truncate: true },
  { key: "edicao", label: "Edição", align: "center" },
  { key: "ano", label: "Ano", align: "center" },
  { key: "inscritos", label: "Inscritos", align: "right" },
  { key: "trabalhos", label: "Trabalhos", align: "right" },
];

const COL_LACUNA: KpiDetailColumn[] = [
  { key: "tipo_lacuna", label: "Tipo", mono: true },
  { key: "secao_documento", label: "Seção" },
  { key: "descricao", label: "Descrição", truncate: true },
  { key: "gravidade", label: "Grav.", align: "center" },
  {
    key: "resolvido",
    label: "Status",
    align: "center",
    format: (v, row) =>
      v ? "Resolvida" : row.virtual ? "APCN" : "Aberta",
  },
];

const COL_EGRESSO: KpiDetailColumn[] = [
  { key: "nome", label: "Egresso" },
  { key: "ano_conclusao", label: "Ano", align: "center" },
  { key: "setor_atuacao", label: "Setor" },
  { key: "atividade_atual", label: "Atividade", truncate: true },
  {
    key: "esta_em_doutorado",
    label: "Doutorado",
    align: "center",
    format: boolSim,
  },
];

const COL_PROD_DOCENTE: KpiDetailColumn[] = [
  { key: "docente", label: "Docente" },
  { key: "linha", label: "Linha" },
  { key: "artigos", label: "Art.", align: "right" },
  { key: "livros", label: "Liv.", align: "right" },
  { key: "capitulos", label: "Cap.", align: "right" },
  { key: "total", label: "Total", align: "right" },
];

const COL_DEMANDA: KpiDetailColumn[] = [
  { key: "ano", label: "Ano", align: "center" },
  { key: "nivel", label: "Nível" },
  { key: "vagas", label: "Vagas", align: "right" },
  { key: "inscritos", label: "Inscritos", align: "right" },
  { key: "matriculados", label: "Matric.", align: "right" },
];

function fmtBrl(n: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    n || 0
  );
}

function producaoByTipo(
  ctx: DossieDataContext,
  field: "artigos" | "livros" | "capitulos" | "anais" | "producao_tecnica" | "total"
): KpiDetailState | null {
  const prod = ctx.producao;
  if (!prod) return null;
  const tabela = rows<Record<string, unknown>>(prod.tabela_por_docente);
  const filtered =
    field === "total"
      ? tabela.filter((r) => Number(r.total ?? 0) > 0)
      : tabela.filter((r) => Number(r[field] ?? 0) > 0);
  const labels: Record<string, string> = {
    artigos: "Artigos",
    livros: "Livros",
    capitulos: "Capítulos",
    anais: "Anais",
    producao_tecnica: "Produção técnica",
    total: "Produção total",
  };
  return {
    title: labels[field],
    subtitle: "Ranking por docente (contagens no período filtrado)",
    columns: COL_PROD_DOCENTE,
    rows: filtered,
    emptyMessage: "Nenhum docente com produção nesta categoria.",
  };
}

function lacunaFilter(
  ctx: DossieDataContext,
  predicate: (r: Record<string, unknown>) => boolean,
  title: string
): KpiDetailState | null {
  const lac = ctx.lacunas;
  if (!lac) return null;
  const tabela = rows<Record<string, unknown>>(lac.tabela);
  const filtered = tabela.filter(predicate);
  return {
    title,
    columns: COL_LACUNA,
    rows: filtered,
    emptyMessage: "Nenhum item nesta categoria.",
  };
}

/** Resolve detalhe localmente (dados já carregados na aba). */
export function resolveDossieKpiDetail(
  kpiId: string,
  ctx: DossieDataContext
): KpiDetailState | null {
  const [section, key] = kpiId.split(".", 2);
  if (!key) return null;

  if (section === "corpo" && ctx.corpo) {
    const tabela = rows<Record<string, unknown>>(ctx.corpo.tabela);
    if (key === "total") {
      return {
        title: "Docentes",
        columns: COL_DOCENTE_LINHA,
        rows: tabela,
      };
    }
    if (key === "linhas") {
      const porLinha = (ctx.corpo.docentes_por_linha as Record<string, number>) || {};
      return {
        title: "Linhas de pesquisa",
        subtitle: "Docentes por linha",
        columns: [
          { key: "linha", label: "Linha" },
          { key: "total", label: "Docentes", align: "right" },
        ],
        rows: Object.entries(porLinha).map(([linha, total]) => ({ linha, total })),
      };
    }
  }

  if (section === "producao") {
    const map: Record<string, KpiDetailState | null> = {
      artigos: producaoByTipo(ctx, "artigos"),
      livros: producaoByTipo(ctx, "livros"),
      capitulos: producaoByTipo(ctx, "capitulos"),
      anais: producaoByTipo(ctx, "anais"),
      tecnica: producaoByTipo(ctx, "producao_tecnica"),
      total: producaoByTipo(ctx, "total"),
    };
    return map[key] ?? null;
  }

  if (section === "projetos" && ctx.projetos) {
    const tabela = rows<Record<string, unknown>>(ctx.projetos.tabela);
    const rels = rows<Record<string, unknown>>(ctx.projetos.tabela_relatorios);
    if (key === "pesquisa") {
      return {
        title: "Projetos de pesquisa",
        columns: COL_PROJETO,
        rows: tabela.filter((r) => String(r.tipo).toLowerCase() === "pesquisa"),
      };
    }
    if (key === "extensao") {
      return {
        title: "Projetos de extensão",
        columns: COL_PROJETO,
        rows: tabela.filter((r) => String(r.tipo).toLowerCase() === "extensao"),
      };
    }
    if (key === "financiamento") {
      return {
        title: "Projetos com financiamento mencionado",
        columns: COL_PROJETO,
        rows: tabela.filter((r) => r.financiamento === "Sim"),
      };
    }
    if (key === "impacto") {
      return {
        title: "Relatórios de impacto regional",
        subtitle: "Projetos e relatórios complementares",
        columns: COL_RELATORIO,
        rows: rels.filter((r) => {
          const t = String(r.tipo_impacto ?? "").toLowerCase();
          return t === "regional" || t === "local";
        }),
      };
    }
    if (key === "todos") {
      return {
        title: "Todos os projetos",
        subtitle: "Pesquisa e extensão no período filtrado",
        columns: COL_PROJETO,
        rows: tabela,
      };
    }
  }

  if (section === "fin" && ctx.financiamento) {
    const matriz = rows<Record<string, unknown>>(ctx.financiamento.matriz_fomento);
    if (key === "confirmados") {
      return {
        title: "Financiamentos confirmados",
        columns: COL_FOMENTO,
        rows: matriz.filter((r) => r.origem === "confirmado"),
      };
    }
    if (key === "mencionados") {
      return {
        title: "Financiamentos mencionados (Lattes)",
        columns: COL_FOMENTO,
        rows: matriz.filter((r) => r.origem === "mencionado"),
      };
    }
    if (key === "aprovado" || key === "executado") {
      return {
        title: key === "aprovado" ? "Linhas com valor aprovado" : "Linhas com valor executado",
        columns: COL_FOMENTO,
        rows: matriz.filter((r) =>
          key === "aprovado"
            ? r.valor_aprovado != null && Number(r.valor_aprovado) > 0
            : r.valor_executado != null && Number(r.valor_executado) > 0
        ),
      };
    }
  }

  if (section === "eventos" && ctx.eventos) {
    const lattes = rows<Record<string, unknown>>(ctx.eventos.tabela);
    const inst = rows<Record<string, unknown>>(ctx.eventos.eventos_institucionais_tabela);
    if (key === "total") {
      return {
        title: "Todos os eventos",
        subtitle: "Lattes + institucionais",
        columns: [
          { key: "_fonte", label: "Fonte", align: "center" },
          ...COL_EVENTO_LATTES,
        ],
        rows: [
          ...lattes.map((r) => ({ ...r, _fonte: "Lattes" })),
          ...inst.map((r) => ({
            _fonte: "Institucional",
            evento: r.nome,
            docente: "—",
            ano: r.ano,
            cidade: r.local ?? "—",
            organizacao: false,
          })),
        ],
      };
    }
    if (key === "institucionais") {
      return { title: "Eventos institucionais", columns: COL_EVENTO_INST, rows: inst };
    }
    if (key === "inscritos" || key === "trabalhos") {
      const field = key === "inscritos" ? "inscritos" : "trabalhos";
      return {
        title: key === "inscritos" ? "Inscrições por evento" : "Trabalhos apresentados",
        columns: COL_EVENTO_INST,
        rows: inst.filter((r) => r[field] != null && Number(r[field]) > 0),
      };
    }
  }

  if (section === "egressos" && ctx.egressos) {
    const tabela = rows<Record<string, unknown>>(ctx.egressos.tabela);
    if (key === "total") {
      return { title: "Egressos", columns: COL_EGRESSO, rows: tabela };
    }
    if (key === "doutorado") {
      return {
        title: "Egressos em doutorado",
        columns: COL_EGRESSO,
        rows: tabela.filter((r) => r.esta_em_doutorado),
      };
    }
    if (key === "ensino") {
      return {
        title: "Egressos no ensino superior",
        columns: COL_EGRESSO,
        rows: tabela.filter((r) => {
          const s = String(r.setor_atuacao ?? "").toLowerCase();
          return s.includes("ensino") || s.includes("universidade");
        }),
      };
    }
    if (key === "municipios") {
      const seen = new Set<string>();
      const munRows: Record<string, unknown>[] = [];
      for (const r of tabela) {
        const city = String(r.cidade_origem ?? r.estado_origem ?? "").trim();
        if (!city || seen.has(city)) continue;
        seen.add(city);
        munRows.push({ municipio: city, egressos: 1 });
      }
      return {
        title: "Municípios alcançados",
        subtitle: "A partir da cidade/estado de origem dos egressos",
        columns: [
          { key: "municipio", label: "Município / UF" },
          { key: "egressos", label: "Registros", align: "right" },
        ],
        rows: munRows,
      };
    }
  }

  if (section === "lacunas") {
    if (key === "abertas") {
      return lacunaFilter(ctx, (r) => !r.resolvido, "Lacunas abertas");
    }
    if (key === "criticas") {
      return lacunaFilter(
        ctx,
        (r) => !r.resolvido && String(r.gravidade) === "alta",
        "Lacunas críticas"
      );
    }
    if (key === "resolvidas") {
      return lacunaFilter(ctx, (r) => Boolean(r.resolvido), "Lacunas resolvidas");
    }
    if (key === "total" && ctx.lacunas) {
      return {
        title: "Todas as lacunas",
        columns: COL_LACUNA,
        rows: rows(ctx.lacunas.tabela),
      };
    }
    if (key === "virtuais") {
      return lacunaFilter(ctx, (r) => Boolean(r.virtual), "Checklist APCN (virtuais)");
    }
  }

  if (section === "demanda" && ctx.demanda) {
    const tabela = rows<Record<string, unknown>>(ctx.demanda.tabela);
    if (key === "inscritos" || key === "vagas" || key === "matriculados") {
      return {
        title: "Processos seletivos",
        subtitle: `Coluna destacada: ${key}`,
        columns: COL_DEMANDA,
        rows: tabela,
      };
    }
  }

  return null;
}

/** KPIs que dependem de endpoint de outra aba (visão geral). */
export const VISAO_KPI_FETCH: Record<
  string,
  { path: string; detailKpiId: string; tab: string }
> = {
  "visao.docentes": { path: "corpo-docente", tab: "corpo", detailKpiId: "corpo.total" },
  "visao.producoes": { path: "producao", tab: "producao", detailKpiId: "producao.total" },
  "visao.projetos": { path: "projetos", tab: "projetos", detailKpiId: "projetos.todos" },
  "visao.eventos": { path: "eventos", tab: "eventos", detailKpiId: "eventos.total" },
  "visao.fomento": { path: "financiamento", tab: "financiamento", detailKpiId: "fin.aprovado" },
  "visao.lacunas": { path: "lacunas", tab: "lacunas", detailKpiId: "lacunas.abertas" },
};

/** Mescla payload de um endpoint no contexto (sem depender de setState). */
export function mergeDossiePathIntoContext(
  ctx: DossieDataContext,
  path: string,
  data: Record<string, unknown>
): DossieDataContext {
  const next = { ...ctx };
  if (path === "corpo-docente") next.corpo = data;
  else if (path === "producao") next.producao = data;
  else if (path === "projetos") next.projetos = data;
  else if (path === "financiamento") next.financiamento = data;
  else if (path === "eventos") next.eventos = data;
  else if (path === "lacunas") next.lacunas = data;
  else if (path === "egressos") next.egressos = data;
  else if (path === "demanda" || path === "visao-geral") {
    if (data.demanda) next.demanda = data.demanda as Record<string, unknown>;
  }
  return next;
}

export function cellValue(
  col: KpiDetailColumn,
  row: Record<string, unknown>
): string {
  const raw = row[col.key];
  if (col.format) return col.format(raw, row);
  return str(raw);
}
