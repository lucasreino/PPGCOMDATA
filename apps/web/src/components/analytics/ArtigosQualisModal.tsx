"use client";

import { useEffect, useMemo, useState } from "react";
import { X, RefreshCw, AlertTriangle, BookOpen, Printer } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { printArtigosQualisInPage } from "@/lib/artigos-qualis-print";
import { SimpleBarChart, StackedBarChart } from "@/components/dossie/charts";

const ESTRATO_COLORS: Record<string, string> = {
  A1: "#10b981",
  A2: "#34d399",
  A3: "#6366f1",
  A4: "#818cf8",
  B1: "#a855f7",
  B2: "#c084fc",
  B3: "#f59e0b",
  B4: "#fbbf24",
  B5: "#f97316",
  C: "#94a3b8",
  "Sem Qualis": "#64748b",
};

export interface ArtigosQualisPayload {
  total_artigos: number;
  total_registros?: number;
  com_qualis: number;
  sem_qualis: number;
  estratos: string[];
  por_estrato: Record<string, { count: number; percent: number }>;
  por_revista: { veiculo: string; count: number; percent: number }[];
  professor_por_estrato: Record<string, Record<string, number>>;
  publicacoes_por_docente?: { docente: string; publicacoes: number }[];
  artigos: {
    id: string;
    professor_id: string;
    professor_nome: string;
    titulo: string;
    veiculo: string;
    qualis: string | null;
    scholar_h5_index?: number | null;
    scholar_h5_median?: number | null;
    scholar_metrics_year?: number | null;
    ano: number | null;
    doi?: string | null;
    docentes_ppgcom?: string[];
    num_docentes_ppgcom?: number;
    eh_coautoria?: boolean;
    autores_lattes?: string | null;
  }[];
}

interface ArtigosQualisModalProps {
  open: boolean;
  onClose: () => void;
  statsProfessorId: string;
  statsLinhaPesquisaId: string;
  statsAnoInicio: string;
  statsAnoFim: string;
  filterSummary?: string;
  previewPorQualis?: Record<string, number>;
}

export function ArtigosQualisModal({
  open,
  onClose,
  statsProfessorId,
  statsLinhaPesquisaId,
  statsAnoInicio,
  statsAnoFim,
  filterSummary,
  previewPorQualis,
}: ArtigosQualisModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ArtigosQualisPayload | null>(null);

  useEffect(() => {
    if (!open) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (statsProfessorId !== "todos") params.set("professor_id", statsProfessorId);
    if (statsLinhaPesquisaId !== "todas") params.set("linha_pesquisa_id", statsLinhaPesquisaId);
    if (statsAnoInicio) params.set("ano_inicio", statsAnoInicio);
    if (statsAnoFim) params.set("ano_fim", statsAnoFim);

    const qs = params.toString();
    apiFetch(qs ? `/analises/artigos/qualis?${qs}` : "/analises/artigos/qualis")
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(
            typeof body.detail === "string" ? body.detail : "Erro ao carregar artigos Qualis"
          );
        }
        return res.json() as Promise<ArtigosQualisPayload>;
      })
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message || "Erro ao carregar");
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [open, statsProfessorId, statsLinhaPesquisaId, statsAnoInicio, statsAnoFim]);

  const estratoBarData = useMemo(() => {
    if (!data) return {};
    const out: Record<string, number> = {};
    for (const [k, v] of Object.entries(data.por_estrato)) {
      out[k] = v.percent;
    }
    return out;
  }, [data]);

  const revistaBarData = useMemo(() => {
    if (!data) return {};
    const out: Record<string, number> = {};
    for (const r of data.por_revista) {
      out[r.veiculo] = r.count;
    }
    return out;
  }, [data]);

  const stackedKeys = data?.estratos ?? [];

  if (!open) return null;

  const canPrint = !loading && !error && data != null;

  return (
    <div
      className="artigos-qualis-modal-overlay fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="artigos-qualis-title"
    >
      <div
        id="artigos-qualis-print-root"
        className="glow-card w-full max-w-5xl max-h-[90vh] flex flex-col rounded-xl border border-slate-200 bg-white shadow-2xl qualis-print-panel"
      >
        <div className="print-only px-5 pt-5 pb-3 border-b border-slate-300 text-slate-800 text-[10pt]">
          <p className="font-bold text-indigo-900 text-sm">PPGCOMDATA — Artigos e estratificação Qualis</p>
          {filterSummary && <p className="mt-1 text-slate-600">{filterSummary}</p>}
          <p className="mt-1 text-slate-500 text-[9pt]">
            Gerado em {new Date().toLocaleString("pt-BR")}
          </p>
        </div>

        <div className="flex items-start justify-between gap-4 p-5 border-b border-slate-200 shrink-0">
          <div>
            <h2
              id="artigos-qualis-title"
              className="text-base font-bold text-slate-900 flex items-center gap-2"
            >
              <BookOpen className="w-5 h-5 text-indigo-400" />
              Artigos — estratificação Qualis
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Obras únicas (coautorias contam uma vez no total). Percentual por estrato, revistas e
              participações por docente.
            </p>
          </div>
          <div className="flex items-center gap-1 shrink-0 no-print">
            <button
              type="button"
              onClick={() => printArtigosQualisInPage()}
              disabled={!canPrint}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-slate-300 border border-slate-700 hover:border-indigo-600 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
              title={canPrint ? "Imprimir este painel" : "Aguarde o carregamento dos dados"}
            >
              <Printer className="w-4 h-4" />
              Imprimir
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100"
              aria-label="Fechar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-6 qualis-print-scroll">
          {loading && (
            <div className="flex flex-col items-center py-16 gap-3 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
              <span className="text-xs">Carregando artigos e estratos Qualis...</span>
            </div>
          )}

          {!loading && error && (
            <div className="flex items-center gap-3 p-4 rounded-lg bg-rose-950/30 border border-rose-800/50 text-rose-200 text-sm">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              {error}
            </div>
          )}

          {!loading && !error && data && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-center">
                  <p className="text-2xl font-bold text-slate-900">{data.total_artigos}</p>
                  <p className="text-[10px] text-slate-500 uppercase font-bold mt-1">
                    Artigos únicos
                  </p>
                  {data.total_registros != null && data.total_registros > data.total_artigos && (
                    <p className="text-[9px] text-slate-600 mt-1">
                      {data.total_registros} registros em currículos
                    </p>
                  )}
                </div>
                <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/20 p-3 text-center">
                  <p className="text-2xl font-bold text-emerald-300">{data.com_qualis}</p>
                  <p className="text-[10px] text-slate-500 uppercase font-bold mt-1">Com Qualis</p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-center">
                  <p className="text-2xl font-bold text-slate-400">{data.sem_qualis}</p>
                  <p className="text-[10px] text-slate-500 uppercase font-bold mt-1">Sem Qualis</p>
                </div>
                <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-center">
                  <p className="text-2xl font-bold text-indigo-300">
                    {data.estratos.filter((e) => e !== "Sem Qualis").length}
                  </p>
                  <p className="text-[10px] text-slate-500 uppercase font-bold mt-1">Estratos</p>
                </div>
              </div>

              {previewPorQualis && Object.keys(previewPorQualis).length > 0 && (
                <p className="text-[10px] text-slate-500">
                  Resumo no card:{" "}
                  {Object.entries(previewPorQualis)
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(" · ")}
                </p>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <section className="rounded-xl border border-slate-200 p-4 space-y-3">
                  <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Percentual por estrato Qualis
                  </h3>
                  {data.total_artigos === 0 ? (
                    <p className="text-xs text-slate-500 py-6 text-center">Nenhum artigo no filtro</p>
                  ) : (
                    <div className="space-y-2">
                      {data.estratos.map((estrato) => {
                        const row = data.por_estrato[estrato];
                        if (!row) return null;
                        const color = ESTRATO_COLORS[estrato] ?? "#6366f1";
                        return (
                          <div key={estrato} className="space-y-1">
                            <div className="flex justify-between text-[11px]">
                              <span className="font-bold text-slate-300">{estrato}</span>
                              <span className="text-slate-400">
                                {row.count} · {row.percent}%
                              </span>
                            </div>
                            <div className="h-2.5 bg-slate-900 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full transition-all"
                                style={{
                                  width: `${Math.min(row.percent, 100)}%`,
                                  backgroundColor: color,
                                }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </section>

                <section className="rounded-xl border border-slate-200 p-4 space-y-3">
                  <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    % por estrato (barras)
                  </h3>
                  <SimpleBarChart
                    data={estratoBarData}
                    maxBars={15}
                    valueFormat={(n) => `${n}%`}
                  />
                </section>
              </div>

              <section className="rounded-xl border border-slate-200 p-4 space-y-3">
                <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  Revistas / periódicos (top)
                </h3>
                <SimpleBarChart data={revistaBarData} maxBars={15} color="#818cf8" />
              </section>

              {Object.keys(data.professor_por_estrato).length > 0 && (
                <section className="rounded-xl border border-slate-200 p-4 space-y-3">
                  <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Docente × estrato Qualis (participações)
                  </h3>
                  <StackedBarChart
                    data={data.professor_por_estrato}
                    keys={stackedKeys}
                    colors={stackedKeys.map((k) => ESTRATO_COLORS[k] ?? "#6366f1")}
                  />
                </section>
              )}

              {(data.publicacoes_por_docente?.length ?? 0) > 0 && (
                <section className="rounded-xl border border-slate-200 p-4 space-y-2">
                  <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Publicações por docente
                  </h3>
                  <ul className="space-y-1 text-xs text-slate-300">
                    {data.publicacoes_por_docente!.map((row) => (
                      <li key={row.docente} className="flex justify-between gap-4">
                        <span className="truncate">{row.docente}</span>
                        <span className="font-bold text-indigo-300 shrink-0">
                          {row.publicacoes}
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              <section className="rounded-xl border border-slate-200 p-4 space-y-3">
                <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  Lista de artigos ({data.artigos.length}
                  {data.total_artigos > data.artigos.length ? ` de ${data.total_artigos}` : ""})
                </h3>
                <ul className="space-y-3 max-h-64 overflow-y-auto pr-1 qualis-print-scroll text-sm">
                  {data.artigos.map((a) => (
                    <li
                      key={`${a.id}-${a.titulo}`}
                      className="p-4 rounded-lg border border-slate-200 bg-white text-slate-700"
                    >
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        {a.qualis ? (
                          <span className="px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-800 font-bold text-[10px]">
                            {a.qualis}
                          </span>
                        ) : (
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-100 text-[10px]">
                            Sem Qualis
                          </span>
                        )}
                        {a.scholar_h5_index != null && (
                          <span
                            className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-900 font-bold text-[10px]"
                            title="Google Scholar Metrics (h5-index)"
                          >
                            h5 {a.scholar_h5_index}
                            {a.scholar_metrics_year != null ? ` · ${a.scholar_metrics_year}` : ""}
                          </span>
                        )}
                        {a.ano != null && (
                          <span className="text-slate-600">{a.ano}</span>
                        )}
                      </div>
                      <p className="font-semibold text-slate-900 leading-snug text-[13px]">{a.titulo}</p>
                      <p className="text-slate-600 mt-1 truncate" title={a.veiculo}>
                        {a.veiculo}
                      </p>
                      {a.eh_coautoria && (a.docentes_ppgcom?.length ?? 0) > 1 ? (
                        <p className="text-slate-700 mt-1">
                          Coautoria PPGCOM ({a.num_docentes_ppgcom}):{" "}
                          {a.docentes_ppgcom!.join(" · ")}
                        </p>
                      ) : (
                        <p className="text-slate-700 mt-1">{a.professor_nome}</p>
                      )}
                      {a.autores_lattes && (
                        <p className="text-slate-600 mt-1 text-xs line-clamp-2">
                          Autores (Lattes): {a.autores_lattes}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
