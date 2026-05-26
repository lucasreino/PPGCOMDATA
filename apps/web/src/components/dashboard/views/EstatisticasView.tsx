"use client";

import React, { useCallback, useState } from "react";
import {
  AlertTriangle,
  Award,
  Calendar,
  FileText,
  RefreshCw,
} from "lucide-react";
import { useDashboard } from "../DashboardProvider";
import { KpiCard } from "@/components/dossie/charts";
import { KpiDetailModal } from "@/components/dossie/KpiDetailModal";
import { apiFetch } from "@/lib/api";
import { cacheKey, cachedJson } from "@/lib/api-cache";
import type { KpiDetailState } from "@/lib/dossie-kpi-detail";
import { EMPTY_DOSSIE_CTX } from "@/lib/dossie-kpi-detail";
import {
  STATS_KPI_FETCH,
  buildStatsDossieQuery,
  mergeStatsFetchIntoContext,
  resolveStatsKpiFromAggregates,
  resolveStatsKpiFromDossie,
} from "@/lib/stats-kpi-detail";

function fmtBRL(n: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n || 0);
}

export function EstatisticasView() {
  const d = useDashboard();
  const [kpiDetail, setKpiDetail] = useState<KpiDetailState | null>(null);
  const [kpiLoading, setKpiLoading] = useState(false);

  const openStatsKpi = useCallback(
    async (kpiId: string) => {
      if (!d.statsData) return;
      setKpiLoading(true);
      try {
        const aggregate = resolveStatsKpiFromAggregates(
          kpiId,
          d.statsData as Record<string, unknown>
        );

        if (!d.apiConnected) {
          if (aggregate) setKpiDetail(aggregate);
          return;
        }

        const spec = STATS_KPI_FETCH[kpiId];
        if (!spec) return;

        const q = buildStatsDossieQuery({
          professorId: d.statsProfessorId,
          linhaId: d.statsLinhaPesquisaId,
          anoInicio: d.statsAnoInicio,
          anoFim: d.statsAnoFim,
        });

        const data = (await cachedJson(
          cacheKey("dossie", "stats-kpi", spec.path, q),
          async () => {
            const res = await apiFetch(`/dossie-apcn/${spec.path}${q}`);
            if (!res.ok) throw new Error(`Falha ao carregar ${spec.path}`);
            return res.json();
          }
        )) as Record<string, unknown>;

        let ctx = mergeStatsFetchIntoContext(EMPTY_DOSSIE_CTX, spec.path, data);
        const detail = resolveStatsKpiFromDossie(kpiId, ctx);
        if (detail) {
          setKpiDetail(detail);
        } else if (aggregate) {
          setKpiDetail(aggregate);
        }
      } catch (err) {
        console.error("Erro ao abrir detalhe do indicador:", err);
        const fallback = resolveStatsKpiFromAggregates(
          kpiId,
          d.statsData as Record<string, unknown>
        );
        if (fallback) setKpiDetail(fallback);
      } finally {
        setKpiLoading(false);
      }
    },
    [
      d.apiConnected,
      d.statsAnoFim,
      d.statsAnoInicio,
      d.statsData,
      d.statsLinhaPesquisaId,
      d.statsProfessorId,
    ]
  );
  return (
        <main className="flex-1 py-6 space-y-6 animate-fadeIn">
          {/* Barra de Filtros */}
          <div className="glow-card rounded-xl p-5 flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px] space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Docente</label>
              <select
                value={d.statsProfessorId}
                onChange={(e) => d.setStatsProfessorId(e.target.value)}
                className="input-field text-xs"
              >
                <option value="todos">Todos os Docentes</option>
                {d.professors.map((p) => (
                  <option key={p.id} value={p.id}>{p.nome_completo}</option>
                ))}
              </select>
            </div>

            <div className="flex-1 min-w-[200px] space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Linha de Pesquisa</label>
              <select
                value={d.statsLinhaPesquisaId}
                onChange={(e) => d.setStatsLinhaPesquisaId(e.target.value)}
                className="input-field text-xs"
              >
                <option value="todas">Todas as Linhas</option>
                {d.linhasPesquisa.map((l) => (
                  <option key={l.id} value={l.id}>{l.nome}</option>
                ))}
              </select>
            </div>

            <div className="w-[110px] space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Início</label>
              <input
                type="number"
                value={d.statsAnoInicio}
                onChange={(e) => d.setStatsAnoInicio(e.target.value)}
                className="input-field text-xs"
              />
            </div>

            <div className="w-[110px] space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Fim</label>
              <input
                type="number"
                value={d.statsAnoFim}
                onChange={(e) => d.setStatsAnoFim(e.target.value)}
                className="input-field text-xs"
              />
            </div>

            <button
              onClick={() => {
                // Force stats refresh
                const currentTab = d.mainTab;
                d.navigateMainTab("validacao");
                setTimeout(() => d.navigateMainTab(currentTab), 50);
              }}
              className="py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-bold text-xs shadow-lg shadow-indigo-600/10 transition-all flex items-center justify-center gap-2 min-h-[38px]"
            >
              <RefreshCw className={`w-4 h-4 ${d.loadingStats ? "animate-spin" : ""}`} />
              Filtrar
            </button>
          </div>

          {d.loadingStats ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-3">
              <RefreshCw className="w-10 h-10 text-indigo-500 animate-spin" />
              <span className="text-xs text-slate-400">Processando e computando agregações estatísticas...</span>
            </div>
          ) : d.statsData ? (
            <div className="space-y-6">
              {/* KPIs Highlights */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-5">
                <KpiCard
                  label="Total de Produções"
                  value={d.statsData.total_producoes}
                  sub="Artigos, livros e capítulos · ranking por docente"
                  accent="indigo"
                  onClick={() => openStatsKpi("stats.producoes")}
                  interactive={kpiLoading}
                />
                <KpiCard
                  label="Fomento Aprovado"
                  value={fmtBRL(d.statsData.fomento_total?.aprovado || 0)}
                  sub="FAPEMA, CNPq, CAPES · linhas com valor aprovado"
                  accent="emerald"
                  onClick={() => openStatsKpi("stats.fomento")}
                  interactive={kpiLoading}
                />
                <KpiCard
                  label="Projetos Ativos"
                  value={d.statsData.total_projetos}
                  sub="Pesquisa e extensão — não inclui grupos CNPq"
                  accent="purple"
                  onClick={() => openStatsKpi("stats.projetos")}
                  interactive={kpiLoading}
                />
                <KpiCard
                  label="Grupos de Pesquisa"
                  value={d.statsData.total_grupos_pesquisa ?? 0}
                  sub="Vínculos em grupos CNPq por docente"
                  accent="rose"
                  onClick={() => openStatsKpi("stats.grupos")}
                  interactive={kpiLoading}
                />
                <KpiCard
                  label="Gaps Pendentes"
                  value={d.statsData.lacunas?.pendentes || 0}
                  sub={`Taxa resolução: ${
                    d.statsData.lacunas?.total > 0
                      ? Math.round(
                          (d.statsData.lacunas.resolvidas / d.statsData.lacunas.total) * 100
                        )
                      : 100
                  }% · lacunas em aberto`}
                  accent="amber"
                  onClick={() => openStatsKpi("stats.lacunas")}
                  interactive={kpiLoading}
                />
              </div>

              {(d.statsData.total_orientacoes != null) && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button
                    type="button"
                    onClick={() => d.setShowOrientacoesModal(true)}
                    className="glow-card rounded-xl p-4 border border-slate-200 text-left w-full cursor-pointer transition-all hover:border-indigo-700/60 hover:bg-indigo-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
                    title="Abrir painel de orientações por professor, tipo, ano e situação"
                  >
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Orientações</span>
                    <p className="text-xl font-bold text-slate-900 mt-1">{d.statsData.total_orientacoes}</p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      {d.statsData.orientacoes_concluidas} concluídas · {d.statsData.orientacoes_em_andamento} em andamento
                      {" · clique para detalhar"}
                    </p>
                  </button>
                  <button
                    type="button"
                    onClick={() => d.setShowArtigosQualisModal(true)}
                    className="glow-card rounded-xl p-4 border border-slate-200 text-left w-full cursor-pointer transition-all hover:border-indigo-700/60 hover:bg-indigo-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
                    title="Abrir painel de artigos por estrato Qualis, revistas e docentes"
                  >
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Qualis (artigos)</span>
                    <p className="text-xl font-bold text-indigo-300 mt-1">
                      {Object.keys(d.statsData.producoes_por_qualis || {}).length} estratos
                    </p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      {Object.entries(d.statsData.producoes_por_qualis || {}).map(([k, v]) => `${k}: ${v}`).join(" · ") || "Sem dados"}
                      {" · clique para gráficos"}
                    </p>
                  </button>
                  <button
                    type="button"
                    onClick={() => d.setShowPendingValidationModal(true)}
                    className="glow-card rounded-xl p-4 border border-slate-200 text-left w-full cursor-pointer transition-all hover:border-amber-700/60 hover:bg-amber-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500/50"
                    title="Ver fila completa de itens aguardando validação"
                  >
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Validação pendente</span>
                    <p className="text-xl font-bold text-amber-300 mt-1">
                      {Object.values(d.statsData.validacao_pendentes || {}).reduce((a: number, b) => a + (b as number), 0)}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      itens aguardando revisão humana · clique para abrir a fila
                    </p>
                  </button>
                </div>
              )}

              {/* Charts Section */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* 1. Evolução Histórica das Produções */}
                <div className="glow-card rounded-xl p-5 space-y-4">
                  <h3 className="text-sm font-semibold tracking-wider text-slate-600 uppercase flex items-center gap-2 border-b border-slate-200 pb-3">
                    <Calendar className="w-4 h-4 text-indigo-400" />
                    Evolução Histórica das Produções
                  </h3>

                  {Object.keys(d.statsData.producoes_por_ano || {}).length === 0 ? (
                    <div className="text-center py-10 text-slate-500 text-xs">Nenhum dado histórico encontrado</div>
                  ) : (
                    <div className="w-full space-y-3 pt-2">
                      {/* Simple Pure React SVG Line Chart with Gradient */}
                      <div className="relative h-44 w-full">
                        <svg className="w-full h-full" viewBox="0 0 500 200" preserveAspectRatio="none">
                          <defs>
                            <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.4" />
                              <stop offset="100%" stopColor="#4f46e5" stopOpacity="0.0" />
                            </linearGradient>
                          </defs>

                          {/* Grid Lines */}
                          <line x1="0" y1="50" x2="500" y2="50" stroke="#cbd5e1" strokeDasharray="3 3" strokeWidth="0.5" />
                          <line x1="0" y1="100" x2="500" y2="100" stroke="#cbd5e1" strokeDasharray="3 3" strokeWidth="0.5" />
                          <line x1="0" y1="150" x2="500" y2="150" stroke="#cbd5e1" strokeDasharray="3 3" strokeWidth="0.5" />

                          {(() => {
                            const years = Object.keys(d.statsData.producoes_por_ano);
                            const values = Object.values(d.statsData.producoes_por_ano) as number[];
                            const maxVal = Math.max(...values, 5);
                            
                            const points = years.map((yr, idx) => {
                              const x = (idx / (years.length - 1)) * 480 + 10;
                              const y = 170 - (values[idx] / maxVal) * 140;
                              return { x, y, value: values[idx], year: yr };
                            });

                            const linePath = points.map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
                            const areaPath = `${linePath} L ${points[points.length - 1].x} 170 L ${points[0].x} 170 Z`;

                            return (
                              <>
                                {/* Filled Area */}
                                <path d={areaPath} fill="url(#lineGrad)" />
                                {/* Smooth Stroke Line */}
                                <path d={linePath} fill="none" stroke="#6366f1" strokeWidth="3.5" strokeLinecap="round" />

                                {/* Dots */}
                                {points.map((p, idx) => (
                                  <g key={idx} className="group cursor-pointer">
                                    <circle
                                      cx={p.x}
                                      cy={p.y}
                                      r="6"
                                      fill="#4f46e5"
                                      stroke="#ffffff"
                                      strokeWidth="2"
                                      className="transition-all duration-200 hover:r-8"
                                    />
                                    <circle
                                      cx={p.x}
                                      cy={p.y}
                                      r="12"
                                      fill="#6366f1"
                                      fillOpacity="0"
                                      className="hover:fill-opacity-20 transition-all duration-200"
                                    />
                                    {/* Mini tooltip for each dot */}
                                    <text
                                      x={p.x}
                                      y={p.y - 12}
                                      fill="#a5b4fc"
                                      fontSize="10"
                                      fontWeight="bold"
                                      textAnchor="middle"
                                      className="opacity-90 bg-slate-900"
                                    >
                                      {p.value}
                                    </text>
                                  </g>
                                ))}
                              </>
                            );
                          })()}
                        </svg>
                      </div>

                      {/* X Axis Labels */}
                      <div className="flex justify-between px-2 text-[10px] text-slate-500 font-bold">
                        {Object.keys(d.statsData.producoes_por_ano).map((yr) => (
                          <span key={yr}>{yr}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* 2. Proporção por Tipo de Produção */}
                <div className="glow-card rounded-xl p-5 space-y-4">
                  <h3 className="text-sm font-semibold tracking-wider text-slate-600 uppercase flex items-center gap-2 border-b border-slate-200 pb-3">
                    <FileText className="w-4 h-4 text-indigo-400" />
                    Mix de Produção Acadêmica
                  </h3>

                  {Object.keys(d.statsData.producoes_por_tipo || {}).length === 0 ? (
                    <div className="text-center py-10 text-slate-500 text-xs">Nenhuma produção registrada</div>
                  ) : (
                    <div className="space-y-4 pt-1">
                      {(() => {
                        const types = Object.keys(d.statsData.producoes_por_tipo);
                        const values = Object.values(d.statsData.producoes_por_tipo) as number[];
                        const total = values.reduce((a, b) => a + b, 0);

                        return types.map((type, idx) => {
                          const val = values[idx];
                          const pct = Math.round((val / total) * 100);
                          
                          // Custom colors based on index
                          const barColors = [
                            "from-indigo-600 to-indigo-400",
                            "from-purple-600 to-purple-400",
                            "from-pink-600 to-pink-400",
                            "from-emerald-600 to-emerald-400",
                            "from-amber-600 to-amber-400"
                          ];

                          return (
                            <div key={type} className="space-y-1.5">
                              <div className="flex justify-between items-center text-xs">
                                <span className="capitalize font-semibold text-slate-300 flex items-center gap-1.5">
                                  <span className={`w-2.5 h-2.5 rounded bg-gradient-to-br ${barColors[idx % barColors.length]}`}></span>
                                  {type === "artigo" ? "Artigos de Periódicos" 
                                   : type === "livro" ? "Livros Publicados" 
                                   : type === "capitulo" ? "Capítulos de Livros" 
                                   : type === "evento" ? "Trabalhos em Eventos" 
                                   : type}
                                </span>
                                <span className="font-bold text-slate-400">
                                  {val} <span className="text-[10px] text-slate-500 font-normal">({pct}%)</span>
                                </span>
                              </div>
                              <div className="w-full bg-slate-50 h-3 rounded-full overflow-hidden border border-slate-200">
                                <div 
                                  className={`bg-gradient-to-r ${barColors[idx % barColors.length]} h-full rounded-full transition-all duration-1000`}
                                  style={{ width: `${pct}%` }}
                                ></div>
                              </div>
                            </div>
                          );
                        });
                      })()}
                    </div>
                  )}
                </div>

                {/* 3. Distribuição de Fomento por Agência Financiadora */}
                <div className="glow-card rounded-xl p-5 space-y-4">
                  <h3 className="text-sm font-semibold tracking-wider text-slate-600 uppercase flex items-center gap-2 border-b border-slate-200 pb-3">
                    <Award className="w-4 h-4 text-indigo-400" />
                    Distribuição de Fomento por Agência
                  </h3>

                  {Object.keys(d.statsData.fomento_por_agencia || {}).length === 0 ? (
                    <div className="text-center py-10 text-slate-500 text-xs">Nenhum fomento/recurso mapeado</div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                      {/* Premium Circle Donut Chart */}
                      <div className="flex justify-center py-2">
                        {(() => {
                          const agencies = Object.keys(d.statsData.fomento_por_agencia);
                          const values = Object.values(d.statsData.fomento_por_agencia) as number[];
                          const total = values.reduce((a, b) => a + b, 0);

                          if (total === 0) return <div className="text-xs text-slate-500 font-semibold">R$ 0,00 Aprovados</div>;

                          let cumulativePercent = 0;
                          const slices = agencies.map((ag, idx) => {
                            const val = values[idx];
                            const percent = (val / total) * 100;
                            const offset = cumulativePercent;
                            cumulativePercent += percent;
                            return { percent, offset, name: ag };
                          });

                          const colorPalette = ["#4f46e5", "#a855f7", "#ec4899", "#10b981", "#f59e0b"];

                          return (
                            <div className="relative w-44 h-44">
                              <svg viewBox="0 0 42 42" className="w-full h-full transform -rotate-90">
                                <circle cx="21" cy="21" r="15.91549430918954" fill="transparent" stroke="#e2e8f0" strokeWidth="4.5" />
                                {slices.map((slice, index) => (
                                  <circle
                                    key={slice.name}
                                    cx="21"
                                    cy="21"
                                    r="15.91549430918954"
                                    fill="transparent"
                                    stroke={colorPalette[index % colorPalette.length]}
                                    strokeWidth="4.8"
                                    strokeDasharray={`${slice.percent} ${100 - slice.percent}`}
                                    strokeDashoffset={100 - slice.offset}
                                    className="transition-all duration-1000 ease-out"
                                  />
                                ))}
                              </svg>
                              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                                <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Aprovado</span>
                                <span className="text-sm font-extrabold text-slate-900 mt-0.5">
                                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(total)}
                                </span>
                              </div>
                            </div>
                          );
                        })()}
                      </div>

                      {/* Legend */}
                      <div className="space-y-3">
                        {(() => {
                          const agencies = Object.keys(d.statsData.fomento_por_agencia);
                          const values = Object.values(d.statsData.fomento_por_agencia) as number[];
                          const total = values.reduce((a, b) => a + b, 0);
                          const colorPalette = ["#4f46e5", "#a855f7", "#ec4899", "#10b981", "#f59e0b"];

                          return agencies.map((ag, idx) => {
                            const val = values[idx];
                            const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                            return (
                              <div key={ag} className="flex justify-between items-center bg-slate-50/40 p-2 border border-slate-200 rounded-lg animate-fadeIn">
                                <div className="flex items-center gap-2">
                                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: colorPalette[idx % colorPalette.length] }}></span>
                                  <span className="text-[11px] font-bold text-slate-300">{ag}</span>
                                </div>
                                <div className="text-[11px] font-bold text-slate-400 text-right">
                                  <span>{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)}</span>
                                  <span className="text-[9px] text-slate-500 font-normal block">{pct}% do fomento</span>
                                </div>
                              </div>
                            );
                          });
                        })()}
                      </div>
                    </div>
                  )}
                </div>

                {/* 4. Gravidade de Alertas & Gaps */}
                <div className="glow-card rounded-xl p-5 space-y-4">
                  <h3 className="text-sm font-semibold tracking-wider text-slate-600 uppercase flex items-center gap-2 border-b border-slate-200 pb-3">
                    <AlertTriangle className="w-4 h-4 text-indigo-400" />
                    Gravidade de Lacunas Pendentes
                  </h3>

                  {d.statsData.lacunas?.total === 0 ? (
                    <div className="text-center py-10 text-slate-500 text-xs">Nenhuma lacuna registrada no sistema</div>
                  ) : (
                    <div className="space-y-4 pt-1">
                      {/* Visual summary of gaps */}
                      <div className="flex bg-slate-50 h-4.5 rounded-full overflow-hidden border border-slate-200 p-0.5">
                        {(() => {
                          const high = d.statsData.lacunas?.por_gravidade?.alta || 0;
                          const med = d.statsData.lacunas?.por_gravidade?.media || 0;
                          const low = d.statsData.lacunas?.por_gravidade?.baixa || 0;
                          const total = high + med + low || 1;

                          const pctH = (high / total) * 100;
                          const pctM = (med / total) * 100;
                          const pctL = (low / total) * 100;

                          return (
                            <>
                              {high > 0 && <div className="bg-rose-500 h-full rounded-l-full" style={{ width: `${pctH}%` }} title={`Alta: ${high}`}></div>}
                              {med > 0 && <div className="bg-amber-500 h-full" style={{ width: `${pctM}%` }} title={`Média: ${med}`}></div>}
                              {low > 0 && <div className="bg-blue-500 h-full rounded-r-full" style={{ width: `${pctL}%` }} title={`Baixa: ${low}`}></div>}
                            </>
                          );
                        })()}
                      </div>

                      {/* Detail list */}
                      <div className="grid grid-cols-3 gap-3">
                        <div className="bg-slate-50/60 p-3 rounded-lg border border-slate-200 text-center">
                          <span className="text-[10px] text-rose-400 font-bold uppercase tracking-wider block">Gravidade Alta</span>
                          <span className="text-xl font-extrabold text-slate-900 block mt-1">{d.statsData.lacunas?.por_gravidade?.alta || 0}</span>
                          <span className="text-[9px] text-slate-500 mt-0.5 block">Exige ação imediata</span>
                        </div>

                        <div className="bg-slate-50/60 p-3 rounded-lg border border-slate-200 text-center">
                          <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider block">Gravidade Média</span>
                          <span className="text-xl font-extrabold text-slate-900 block mt-1">{d.statsData.lacunas?.por_gravidade?.media || 0}</span>
                          <span className="text-[9px] text-slate-500 mt-0.5 block">Revisão recomendada</span>
                        </div>

                        <div className="bg-slate-50/60 p-3 rounded-lg border border-slate-200 text-center">
                          <span className="text-[10px] text-blue-400 font-bold uppercase tracking-wider block">Gravidade Baixa</span>
                          <span className="text-xl font-extrabold text-slate-900 block mt-1">{d.statsData.lacunas?.por_gravidade?.baixa || 0}</span>
                          <span className="text-[9px] text-slate-500 mt-0.5 block">Ajustes informacionais</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

              </div>
            </div>
          ) : (
            <div className="text-center py-16 text-slate-500 text-xs">Nenhum dado analítico pôde ser computado</div>
          )}

          <KpiDetailModal detail={kpiDetail} onClose={() => setKpiDetail(null)} />
        </main>
  );
}
