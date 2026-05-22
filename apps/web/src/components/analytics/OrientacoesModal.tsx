"use client";

import { useEffect, useMemo, useState } from "react";
import { X, RefreshCw, AlertTriangle, Users, Printer } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { printOrientacoesInPage } from "@/lib/orientacoes-print";
import { SimpleBarChart, StackedBarChart } from "@/components/dossie/charts";

const TIPO_COLORS: Record<string, string> = {
  doutorado: "#6366f1",
  mestrado: "#818cf8",
  pos_doutorado: "#a855f7",
  ic: "#34d399",
  tcc: "#f59e0b",
  outra: "#94a3b8",
};

const STATUS_COLORS: Record<string, string> = {
  concluida: "#10b981",
  em_andamento: "#f59e0b",
};

export interface OrientacaoItem {
  id: string;
  professor_id: string;
  professor_nome: string;
  tipo: string;
  tipo_label: string;
  status: string;
  status_label: string;
  nome_orientando: string | null;
  titulo_trabalho: string | null;
  instituicao: string | null;
  ano_inicio: number | null;
  ano_conclusao: number | null;
  ano_referencia: number | null;
  papel: string;
}

export interface OrientacaoGrupo {
  key: string;
  label: string;
  count: number;
  items: OrientacaoItem[];
}

export interface OrientacoesPayload {
  total: number;
  concluidas: number;
  em_andamento: number;
  tipos: string[];
  por_tipo: { tipo: string; label: string; count: number; percent: number }[];
  por_status: { status: string; label: string; count: number; percent: number }[];
  por_ano: { ano: number; count: number; percent: number }[];
  professor_por_tipo: Record<string, Record<string, number>>;
  por_tipo_grupos: OrientacaoGrupo[];
  por_status_grupos: OrientacaoGrupo[];
  por_ano_grupos: OrientacaoGrupo[];
  por_professor_grupos: OrientacaoGrupo[];
  orientacoes: OrientacaoItem[];
}

interface OrientacoesModalProps {
  open: boolean;
  onClose: () => void;
  statsProfessorId: string;
  statsLinhaPesquisaId: string;
  statsAnoInicio: string;
  statsAnoFim: string;
  filterSummary?: string;
}

function OrientacaoListItem({ item }: { item: OrientacaoItem }) {
  const periodo =
    item.ano_inicio && item.ano_conclusao
      ? `${item.ano_inicio}–${item.ano_conclusao}`
      : item.ano_conclusao
        ? String(item.ano_conclusao)
        : item.ano_inicio
          ? `desde ${item.ano_inicio}`
          : null;

  return (
    <li className="p-3 rounded-lg border border-slate-800 bg-slate-950/40 text-xs">
      <div className="flex flex-wrap items-center gap-2 mb-1">
        <span
          className="px-1.5 py-0.5 rounded font-bold text-[10px]"
          style={{
            backgroundColor: `${TIPO_COLORS[item.tipo] ?? "#6366f1"}22`,
            color: TIPO_COLORS[item.tipo] ?? "#818cf8",
          }}
        >
          {item.tipo_label}
        </span>
        <span
          className="px-1.5 py-0.5 rounded text-[10px] font-bold"
          style={{
            backgroundColor: `${STATUS_COLORS[item.status] ?? "#64748b"}22`,
            color: STATUS_COLORS[item.status] ?? "#94a3b8",
          }}
        >
          {item.status_label}
        </span>
        {periodo && <span className="text-slate-500">{periodo}</span>}
      </div>
      <p className="font-semibold text-slate-200 leading-snug">
        {item.nome_orientando || "Orientando não identificado"}
      </p>
      {item.titulo_trabalho && (
        <p className="text-slate-400 mt-1 leading-snug">{item.titulo_trabalho}</p>
      )}
      {item.instituicao && <p className="text-slate-500 mt-1">{item.instituicao}</p>}
      <p className="text-slate-600 mt-0.5">{item.professor_nome}</p>
    </li>
  );
}

function GrupoSection({
  title,
  grupos,
  emptyMessage,
}: {
  title: string;
  grupos: OrientacaoGrupo[];
  emptyMessage: string;
}) {
  return (
    <section className="rounded-xl border border-slate-800 p-4 space-y-4">
      <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{title}</h3>
      {grupos.length === 0 ? (
        <p className="text-xs text-slate-500 py-4 text-center">{emptyMessage}</p>
      ) : (
        grupos.map((g) => (
          <div key={g.key} className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <h4 className="text-sm font-bold text-slate-200">{g.label}</h4>
              <span className="text-[10px] text-slate-500 font-mono">{g.count}</span>
            </div>
            <ul className="space-y-2 orientacoes-print-scroll">
              {g.items.map((item) => (
                <OrientacaoListItem key={item.id} item={item} />
              ))}
            </ul>
          </div>
        ))
      )}
    </section>
  );
}

export function OrientacoesModal({
  open,
  onClose,
  statsProfessorId,
  statsLinhaPesquisaId,
  statsAnoInicio,
  statsAnoFim,
  filterSummary,
}: OrientacoesModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<OrientacoesPayload | null>(null);

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
    apiFetch(qs ? `/analises/orientacoes/painel?${qs}` : "/analises/orientacoes/painel")
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(
            typeof body.detail === "string" ? body.detail : "Erro ao carregar orientações"
          );
        }
        return res.json() as Promise<OrientacoesPayload>;
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

  const tipoBarData = useMemo(() => {
    if (!data) return {};
    const out: Record<string, number> = {};
    for (const row of data.por_tipo) out[row.label] = row.count;
    return out;
  }, [data]);

  const statusBarData = useMemo(() => {
    if (!data) return {};
    const out: Record<string, number> = {};
    for (const row of data.por_status) out[row.label] = row.count;
    return out;
  }, [data]);

  const anoBarData = useMemo(() => {
    if (!data) return {};
    const out: Record<string, number> = {};
    for (const row of data.por_ano) out[String(row.ano)] = row.count;
    return out;
  }, [data]);

  const stackedKeys = data?.tipos ?? [];

  if (!open) return null;

  const canPrint = !loading && !error && data != null;

  return (
    <div
      className="orientacoes-modal-overlay fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="orientacoes-title"
    >
      <div
        id="orientacoes-print-root"
        className="glow-card w-full max-w-5xl max-h-[90vh] flex flex-col rounded-xl border border-slate-800 bg-[#0f172a] shadow-2xl"
      >
        <div className="print-only px-5 pt-5 pb-3 border-b border-slate-300 text-slate-800 text-[10pt]">
          <p className="font-bold text-indigo-900 text-sm">PPGCOMDATA — Orientações</p>
          {filterSummary && <p className="mt-1 text-slate-600">{filterSummary}</p>}
          <p className="mt-1 text-slate-500 text-[9pt]">
            Gerado em {new Date().toLocaleString("pt-BR")}
          </p>
        </div>

        <div className="flex items-start justify-between gap-4 p-5 border-b border-slate-800 shrink-0">
          <div>
            <h2
              id="orientacoes-title"
              className="text-base font-bold text-white flex items-center gap-2"
            >
              <Users className="w-5 h-5 text-indigo-400" />
              Orientações — detalhamento
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Por professor, tipo, ano e situação (concluídas / em andamento)
            </p>
          </div>
          <div className="flex items-center gap-1 shrink-0 no-print">
            <button
              type="button"
              onClick={() => printOrientacoesInPage()}
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
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              aria-label="Fechar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-6 orientacoes-print-scroll">
          {loading && (
            <div className="flex flex-col items-center py-16 gap-3 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
              <span className="text-xs">Carregando orientações...</span>
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
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3 text-center">
                  <p className="text-2xl font-bold text-white">{data.total}</p>
                  <p className="text-[10px] text-slate-500 uppercase font-bold mt-1">Total</p>
                </div>
                <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/20 p-3 text-center">
                  <p className="text-2xl font-bold text-emerald-300">{data.concluidas}</p>
                  <p className="text-[10px] text-slate-500 uppercase font-bold mt-1">Concluídas</p>
                </div>
                <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-3 text-center">
                  <p className="text-2xl font-bold text-amber-300">{data.em_andamento}</p>
                  <p className="text-[10px] text-slate-500 uppercase font-bold mt-1">
                    Em andamento
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                <section className="rounded-xl border border-slate-800 p-4 space-y-3">
                  <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Por tipo
                  </h3>
                  <SimpleBarChart data={tipoBarData} maxBars={12} color="#818cf8" />
                </section>
                <section className="rounded-xl border border-slate-800 p-4 space-y-3">
                  <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Concluídas × em andamento
                  </h3>
                  <SimpleBarChart data={statusBarData} maxBars={5} color="#10b981" />
                </section>
                <section className="rounded-xl border border-slate-800 p-4 space-y-3">
                  <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Por ano
                  </h3>
                  <SimpleBarChart data={anoBarData} maxBars={12} color="#a855f7" />
                </section>
              </div>

              {Object.keys(data.professor_por_tipo).length > 0 && (
                <section className="rounded-xl border border-slate-800 p-4 space-y-3">
                  <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Docente × tipo de orientação
                  </h3>
                  <StackedBarChart
                    data={data.professor_por_tipo}
                    keys={stackedKeys}
                    colors={stackedKeys.map((k) => TIPO_COLORS[k] ?? "#6366f1")}
                  />
                </section>
              )}

              <GrupoSection
                title="Por professor"
                grupos={data.por_professor_grupos}
                emptyMessage="Nenhuma orientação no filtro"
              />
              <GrupoSection
                title="Por tipo de orientação"
                grupos={data.por_tipo_grupos}
                emptyMessage="Nenhuma orientação no filtro"
              />
              <GrupoSection
                title="Por ano (conclusão ou início)"
                grupos={data.por_ano_grupos}
                emptyMessage="Nenhuma orientação com ano informado"
              />
              <GrupoSection
                title="Por situação — concluídas e em andamento"
                grupos={data.por_status_grupos}
                emptyMessage="Nenhuma orientação no filtro"
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
