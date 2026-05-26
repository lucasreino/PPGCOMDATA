import type { KpiDetailColumn, KpiDetailState } from "./dossie-kpi-detail";
import {
  mergeDossiePathIntoContext,
  resolveDossieKpiDetail,
  type DossieDataContext,
} from "./dossie-kpi-detail";

export type StatsFilterState = {
  professorId: string;
  linhaId: string;
  anoInicio: string;
  anoFim: string;
};

/** KPIs da aba Indicadores → endpoint dossiê + resolver de detalhe. */
export const STATS_KPI_FETCH: Record<
  string,
  { path: string; detailKpiId: string }
> = {
  "stats.producoes": { path: "producao", detailKpiId: "producao.total" },
  "stats.fomento": { path: "financiamento", detailKpiId: "fin.aprovado" },
  "stats.projetos": { path: "projetos", detailKpiId: "projetos.todos" },
  "stats.grupos": { path: "grupos-pesquisa", detailKpiId: "grupos.total" },
  "stats.lacunas": { path: "lacunas", detailKpiId: "lacunas.abertas" },
};

const COL_BREAKDOWN: KpiDetailColumn[] = [
  { key: "nome", label: "Categoria" },
  { key: "valor", label: "Quantidade", align: "right" },
];

const COL_FOMENTO_AGENCIA: KpiDetailColumn[] = [
  { key: "agencia", label: "Agência" },
  {
    key: "valor",
    label: "Aprovado (R$)",
    align: "right",
    format: (v) =>
      new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
        Number(v) || 0
      ),
  },
];

const COL_LACUNA_GRAV: KpiDetailColumn[] = [
  { key: "gravidade", label: "Gravidade" },
  { key: "total", label: "Lacunas", align: "right" },
];

function mapCountRecord(
  rec: Record<string, number> | undefined,
  labelKey = "nome"
): Record<string, unknown>[] {
  if (!rec) return [];
  return Object.entries(rec).map(([nome, valor]) => ({
    [labelKey]: nome,
    valor,
  }));
}

/** Detalhe imediato a partir de agregados de `/analises/estatisticas` (offline ou fallback). */
export function resolveStatsKpiFromAggregates(
  kpiId: string,
  stats: Record<string, unknown>
): KpiDetailState | null {
  if (kpiId === "stats.producoes") {
    const porTipo = stats.producoes_por_tipo as Record<string, number> | undefined;
    const rows = mapCountRecord(porTipo).map((r) => ({
      nome:
        r.nome === "artigo"
          ? "Artigos de periódicos"
          : r.nome === "livro"
            ? "Livros"
            : r.nome === "capitulo"
              ? "Capítulos"
              : r.nome === "evento"
                ? "Trabalhos em eventos"
                : String(r.nome),
      valor: r.valor,
    }));
    return {
      title: "Produções por tipo",
      subtitle: "Resumo agregado (lista por docente requer conexão com a API)",
      columns: COL_BREAKDOWN,
      rows,
      emptyMessage: "Nenhuma produção no período filtrado.",
    };
  }

  if (kpiId === "stats.fomento") {
    const porAgencia = stats.fomento_por_agencia as Record<string, number> | undefined;
    return {
      title: "Fomento aprovado por agência",
      subtitle: "Valores agregados do painel de indicadores",
      columns: COL_FOMENTO_AGENCIA,
      rows: Object.entries(porAgencia || {}).map(([agencia, valor]) => ({
        agencia,
        valor,
      })),
      emptyMessage: "Nenhum fomento aprovado no período.",
    };
  }

  if (kpiId === "stats.projetos") {
    const porSituacao = stats.projetos_por_situacao as Record<string, number> | undefined;
    return {
      title: "Projetos por situação",
      subtitle:
        "Projetos de pesquisa/extensão — não inclui grupos CNPq (lista via API dossiê)",
      columns: COL_BREAKDOWN,
      rows: mapCountRecord(porSituacao),
      emptyMessage: "Nenhum projeto no período filtrado.",
    };
  }

  if (kpiId === "stats.grupos") {
    const total = Number(stats.total_grupos_pesquisa ?? 0);
    return {
      title: "Grupos de pesquisa",
      subtitle:
        total > 0
          ? `${total} vínculo(s) em grupo — detalhes por docente via API`
          : "Vínculos em grupos CNPq (distinto de projetos)",
      columns: COL_BREAKDOWN,
      rows: [{ nome: "Total de vínculos em grupo", valor: total }],
      emptyMessage: "Nenhum grupo cadastrado.",
    };
  }

  if (kpiId === "stats.lacunas") {
    const lac = stats.lacunas as
      | { por_gravidade?: Record<string, number>; pendentes?: number }
      | undefined;
    const porGrav = lac?.por_gravidade || {};
    const rows = Object.entries(porGrav).map(([gravidade, total]) => ({
      gravidade:
        gravidade === "alta"
          ? "Alta"
          : gravidade === "media"
            ? "Média"
            : gravidade === "baixa"
              ? "Baixa"
              : gravidade,
      total,
    }));
    return {
      title: "Lacunas pendentes por gravidade",
      subtitle:
        lac?.pendentes != null
          ? `${lac.pendentes} lacuna(s) em aberto no total`
          : "Resumo agregado",
      columns: COL_LACUNA_GRAV,
      rows,
      emptyMessage: "Nenhuma lacuna pendente.",
    };
  }

  return null;
}

export function buildStatsDossieQuery(f: StatsFilterState): string {
  const q = new URLSearchParams();
  if (f.professorId && f.professorId !== "todos") {
    q.set("professor_id", f.professorId);
  }
  if (f.linhaId && f.linhaId !== "todas") {
    q.set("linha_pesquisa_id", f.linhaId);
  }
  if (f.anoInicio) q.set("ano_inicio", f.anoInicio);
  if (f.anoFim) q.set("ano_fim", f.anoFim);
  const s = q.toString();
  return s ? `?${s}` : "";
}

/** Resolve detalhe após carregar payload do dossiê (lista item a item). */
export function resolveStatsKpiFromDossie(
  kpiId: string,
  ctx: DossieDataContext
): KpiDetailState | null {
  const spec = STATS_KPI_FETCH[kpiId];
  if (!spec) return null;
  return resolveDossieKpiDetail(spec.detailKpiId, ctx);
}

export function mergeStatsFetchIntoContext(
  ctx: DossieDataContext,
  path: string,
  data: Record<string, unknown>
): DossieDataContext {
  return mergeDossiePathIntoContext(ctx, path, data);
}
