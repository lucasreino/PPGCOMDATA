// @ts-nocheck — payloads dinâmicos do dossiê APCN
"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Suspense } from "react";
import { AppShellHeader } from "@/components/layout/AppShellHeader";
import {
  AlertTriangle,
  BarChart2,
  BookOpen,
  Calendar,
  DollarSign,
  Download,
  FileText,
  GraduationCap,
  LayoutDashboard,
  Users,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/lib/api";
import {
  DossieFiltersBar,
  buildDossieQuery,
  type FilterState,
} from "@/components/dossie/DossieFilters";
import {
  ChartPanel,
  KpiCard,
  SimpleBarChart,
  SimpleLineChart,
  StackedBarChart,
} from "@/components/dossie/charts";
import { downloadChartPng } from "@/lib/chartExport";
import { CatalogPanel, ExportButtons } from "@/components/dossie/CatalogPanel";
import { RelatorioForm } from "@/components/dossie/RelatorioForm";

const TABS = [
  { id: "visao", label: "Visão Geral", icon: LayoutDashboard },
  { id: "corpo", label: "Corpo Docente", icon: Users },
  { id: "producao", label: "Produção Intelectual", icon: FileText },
  { id: "projetos", label: "Projetos e Extensão", icon: BookOpen },
  { id: "financiamento", label: "Financiamento", icon: DollarSign },
  { id: "eventos", label: "Eventos", icon: Calendar },
  { id: "egressos", label: "Egressos e Impacto", icon: GraduationCap },
  { id: "lacunas", label: "Lacunas", icon: AlertTriangle },
  { id: "exportacoes", label: "Exportações", icon: Download },
] as const;

type TabId = (typeof TABS)[number]["id"];

const defaultFilters: FilterState = {
  professorId: "",
  linhaId: "",
  anoInicio: "2015",
  anoFim: "2026",
  apenasValidados: false,
};

function fmtBRL(n: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n || 0);
}

export default function DossieApcnPage() {
  const { user, loading: authLoading } = useAuth();
  const [tab, setTab] = useState<TabId>("visao");
  const [filters, setFilters] = useState<FilterState>(defaultFilters);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [professores, setProfessores] = useState<{ id: string; nome_completo: string }[]>([]);
  const [linhas, setLinhas] = useState<{ id: string; nome: string }[]>([]);

  const [overview, setOverview] = useState<Record<string, unknown> | null>(null);
  const [corpo, setCorpo] = useState<Record<string, unknown> | null>(null);
  const [producao, setProducao] = useState<Record<string, unknown> | null>(null);
  const [projetos, setProjetos] = useState<Record<string, unknown> | null>(null);
  const [financiamento, setFinanciamento] = useState<Record<string, unknown> | null>(null);
  const [eventos, setEventos] = useState<Record<string, unknown> | null>(null);
  const [lacunas, setLacunas] = useState<Record<string, unknown> | null>(null);
  const [egressos, setEgressos] = useState<Record<string, unknown> | null>(null);
  const [demanda, setDemanda] = useState<Record<string, unknown> | null>(null);
  const [narrativas, setNarrativas] = useState<Record<string, string> | null>(null);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      apiFetch("/professores").then((r) => (r.ok ? r.json() : [])),
      apiFetch("/linhas-pesquisa").then((r) => (r.ok ? r.json() : [])),
    ]).then(([p, l]) => {
      setProfessores(Array.isArray(p) ? p : []);
      setLinhas(Array.isArray(l) ? l : []);
    });
  }, [user]);

  const parseRes = async (res: Response, name: string) => {
    if (!res.ok) throw new Error(`Falha ao carregar ${name}`);
    return res.json();
  };

  const loadTabData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    const q = buildDossieQuery(filters);
    const pathsByTab: Record<TabId, string[]> = {
      visao: ["visao-geral"],
      corpo: ["corpo-docente"],
      producao: ["producao"],
      projetos: ["projetos"],
      financiamento: ["financiamento"],
      eventos: ["eventos"],
      egressos: ["egressos"],
      lacunas: ["lacunas"],
      exportacoes: ["overview"],
    };
    const paths = pathsByTab[tab] ?? ["overview"];
    try {
      const responses = await Promise.all(
        paths.map((p) => apiFetch(`/dossie-apcn/${p}${q}`))
      );
      for (let i = 0; i < paths.length; i++) {
        const path = paths[i];
        const data = await parseRes(responses[i], path);
        if (path === "visao-geral") {
          setOverview(data.overview ?? data);
          setDemanda(data.demanda ?? null);
          setNarrativas(data.narrativas ?? null);
        } else if (path === "overview") setOverview(data);
        else if (path === "corpo-docente") setCorpo(data);
        else if (path === "producao") setProducao(data);
        else if (path === "projetos") setProjetos(data);
        else if (path === "financiamento") setFinanciamento(data);
        else if (path === "eventos") setEventos(data);
        else if (path === "lacunas") setLacunas(data);
        else if (path === "egressos") setEgressos(data);
        else if (path === "demanda") setDemanda(data);
        else if (path === "narrativas") setNarrativas(data);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar indicadores");
    } finally {
      setLoading(false);
    }
  }, [user, filters, tab]);

  const loadData = loadTabData;

  useEffect(() => {
    if (user) loadTabData();
  }, [user, loadTabData]);

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-600 text-sm">
        Carregando sessão...
      </div>
    );
  }

  type DossiePayload = Record<string, unknown>;

  const ov = overview as DossiePayload | null;
  const prod = producao as DossiePayload | null;
  const fin = financiamento as DossiePayload | null;
  const lac = lacunas as DossiePayload | null;

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Suspense fallback={<header className="border-b border-slate-200 h-[120px] animate-pulse bg-white" />}>
        <AppShellHeader section="dossie" />
      </Suspense>

      <div className="border-b border-slate-200 bg-white">
        <div className="max-w-[1400px] mx-auto w-full px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs text-slate-600">
            Proposta de Doutorado — PPGCOM · visão institucional
          </p>
          <span className="text-[10px] px-3 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700">
            Dados reais do banco
          </span>
        </div>
        <div className="max-w-[1400px] mx-auto w-full px-4 sm:px-6 flex flex-wrap gap-1 pb-3 overflow-x-auto">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setTab(id)}
              className={`px-3 py-2 rounded-lg text-[11px] font-bold whitespace-nowrap flex items-center gap-1.5 transition-all ${
                tab === id
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 hover:text-slate-900 bg-white border border-slate-200 hover:bg-slate-50"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>
      </div>

      <main className="flex-1 py-6 space-y-6 max-w-[1400px] mx-auto w-full px-4 sm:px-6">
        <DossieFiltersBar
          filters={filters}
          onChange={setFilters}
          onRefresh={loadData}
          loading={loading}
          professores={professores}
          linhas={linhas}
        />

        {error && (
          <div className="rounded-lg border border-rose-200 bg-rose-50 text-rose-700 text-sm px-4 py-3">
            {error}
          </div>
        )}

        {loading && !overview ? (
          <div className="text-center py-20 text-slate-600 text-sm">Carregando indicadores...</div>
        ) : (
          <>
            {tab === "visao" && ov && (
              <section className="space-y-6 animate-fadeIn">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <KpiCard label="Docentes" value={ov.total_docentes ?? 0} accent="indigo" />
                  <KpiCard label="Produções" value={ov.total_producoes ?? 0} accent="purple" />
                  <KpiCard
                    label="Fomento aprovado"
                    value={fmtBRL(ov.fomento_total?.aprovado ?? 0)}
                    accent="emerald"
                  />
                  <KpiCard label="Lacunas abertas" value={ov.lacunas_pendentes ?? 0} accent="amber" />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <KpiCard label="Projetos" value={ov.total_projetos ?? 0} />
                  <KpiCard label="Eventos" value={ov.total_eventos ?? 0} />
                  <KpiCard label="Orientações" value={ov.total_orientacoes ?? 0} />
                  <KpiCard
                    label="Validação pendente"
                    value={ov.validacao_pendentes ?? 0}
                    sub="itens aguardando revisão"
                    accent="amber"
                  />
                </div>
                {prod?.producao_por_ano && Object.keys(prod.producao_por_ano).length > 0 && (
                  <ChartPanel
                    title="Produção por ano"
                    exportSpec={{
                      kind: "line",
                      title: "Produção por ano",
                      data: prod.producao_por_ano as Record<string, number>,
                    }}
                  >
                    <SimpleLineChart data={prod.producao_por_ano as Record<string, number>} />
                  </ChartPanel>
                )}
                {demanda && (demanda.por_ano as Record<string, Record<string, number>>) && (
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-900 mb-3">Demanda discente por ano</h3>
                    <StackedBarChart
                      data={Object.fromEntries(
                        Object.entries(demanda.por_ano as Record<string, Record<string, number>>).map(
                          ([ano, v]) => [ano, { inscritos: v.inscritos, vagas: v.vagas }]
                        )
                      )}
                      keys={["inscritos", "vagas"]}
                      colors={["#6366f1", "#94a3b8"]}
                    />
                  </div>
                )}
                {demanda && (demanda.total_processos as number) > 0 && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <KpiCard label="Inscritos (seleção)" value={demanda.total_inscritos as number} />
                    <KpiCard label="Vagas" value={demanda.total_vagas as number} />
                    <KpiCard
                      label="Candidato/vaga"
                      value={demanda.relacao_media_candidato_vaga as number}
                    />
                    <KpiCard label="Matriculados" value={demanda.total_matriculados as number} accent="emerald" />
                  </div>
                )}
                {narrativas?.visao_geral && (
                  <div className="glow-card rounded-xl p-5 text-sm text-slate-700 leading-relaxed">
                    {narrativas.visao_geral}
                  </div>
                )}
              </section>
            )}

            {tab === "corpo" && corpo && (
              <section className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <KpiCard label="Total docentes" value={(corpo.total_docentes as number) ?? 0} />
                  <KpiCard
                    label="Linhas representadas"
                    value={Object.keys((corpo.docentes_por_linha as Record<string, number>) || {}).length}
                  />
                </div>
                <div className="glow-card rounded-xl overflow-hidden">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-100 text-slate-600 uppercase text-[10px]">
                      <tr>
                        <th className="text-left p-3">Docente</th>
                        <th className="text-left p-3">Linha</th>
                        <th className="text-right p-3">Produções</th>
                        <th className="text-right p-3">Projetos</th>
                        <th className="text-right p-3">Lacunas</th>
                      </tr>
                    </thead>
                    <tbody>
                      {((corpo.tabela as Array<Record<string, unknown>>) || []).map((row) => (
                        <tr key={String(row.id)} className="border-t border-slate-200 hover:bg-slate-50">
                          <td className="p-3 text-slate-900 font-medium">{String(row.nome)}</td>
                          <td className="p-3 text-slate-600">{String(row.linha)}</td>
                          <td className="p-3 text-right text-indigo-600">{String(row.producoes)}</td>
                          <td className="p-3 text-right text-slate-700">{String(row.projetos)}</td>
                          <td className="p-3 text-right text-amber-600">{String(row.lacunas_abertas)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {tab === "producao" && prod && (
              <section className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  {[
                    ["Artigos", prod.totais?.artigos],
                    ["Livros", prod.totais?.livros],
                    ["Capítulos", prod.totais?.capitulos],
                    ["Anais", prod.totais?.anais],
                    ["Prod. técnica", prod.totais?.producao_tecnica],
                    ["Total", prod.totais?.total],
                  ].map(([label, val]) => (
                    <KpiCard key={String(label)} label={String(label)} value={val ?? 0} />
                  ))}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <ChartPanel
                    title="Por docente"
                    exportSpec={{
                      kind: "bar",
                      title: "Produção por docente",
                      data: (prod.producao_por_docente as Record<string, number>) || {},
                    }}
                  >
                    <SimpleBarChart data={prod.producao_por_docente || {}} />
                  </ChartPanel>
                  <ChartPanel
                    title="Por tipo"
                    exportSpec={{
                      kind: "bar",
                      title: "Produção por tipo",
                      data: (prod.producao_por_tipo as Record<string, number>) || {},
                      color: "#a855f7",
                    }}
                  >
                    <SimpleBarChart data={prod.producao_por_tipo || {}} color="#a855f7" />
                  </ChartPanel>
                </div>
                <ChartPanel
                  title="Evolução por ano"
                  exportSpec={{
                    kind: "line",
                    title: "Evolução da produção",
                    data: (prod.producao_por_ano as Record<string, number>) || {},
                  }}
                >
                  <SimpleLineChart data={prod.producao_por_ano || {}} />
                </ChartPanel>
                {(prod.producao_por_linha_e_tipo as Record<string, Record<string, number>>) &&
                  Object.keys(prod.producao_por_linha_e_tipo as object).length > 0 && (
                    <div className="glow-card rounded-xl p-5">
                      <h3 className="text-sm font-semibold text-slate-900 mb-3">
                        Produção por linha e tipo
                      </h3>
                      <StackedBarChart
                        data={prod.producao_por_linha_e_tipo as Record<string, Record<string, number>>}
                        keys={["artigos", "livros", "capitulos", "anais", "producao_tecnica"]}
                      />
                    </div>
                  )}
                <div className="glow-card rounded-xl overflow-x-auto">
                  <table className="w-full text-xs min-w-[700px]">
                    <thead className="bg-slate-100 text-slate-600 text-[10px] uppercase">
                      <tr>
                        {["Docente", "Linha", "Art.", "Liv.", "Cap.", "Anais", "Téc.", "Total", "Pend."].map(
                          (h) => (
                            <th key={h} className={`p-3 ${h === "Docente" || h === "Linha" ? "text-left" : "text-right"}`}>
                              {h}
                            </th>
                          )
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {(prod.tabela_por_docente || []).map((row) => (
                        <tr key={String(row.professor_id)} className="border-t border-slate-200">
                          <td className="p-3 text-slate-900 font-medium">{String(row.docente)}</td>
                          <td className="p-3 text-slate-600">{String(row.linha)}</td>
                          <td className="p-3 text-right text-slate-700">{row.artigos}</td>
                          <td className="p-3 text-right text-slate-700">{row.livros}</td>
                          <td className="p-3 text-right text-slate-700">{row.capitulos}</td>
                          <td className="p-3 text-right text-slate-700">{row.anais}</td>
                          <td className="p-3 text-right text-slate-700">{row.producao_tecnica}</td>
                          <td className="p-3 text-right font-bold text-indigo-600">{row.total}</td>
                          <td className="p-3 text-right text-amber-600">{row.pendencias}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {tab === "projetos" && projetos && (
              <section className="space-y-6">
                <RelatorioForm professores={professores} linhas={linhas} onSaved={loadData} />
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <KpiCard label="Pesquisa" value={(projetos.total_projetos_pesquisa as number) ?? 0} />
                  <KpiCard label="Extensão" value={(projetos.total_projetos_extensao as number) ?? 0} accent="emerald" />
                  <KpiCard label="Com financiamento" value={(projetos.projetos_com_financiamento as number) ?? 0} />
                  <KpiCard
                    label="Impacto regional"
                    value={(projetos.projetos_impacto_regional as number) ?? 0}
                    accent="emerald"
                  />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-900 mb-3">Pesquisa × extensão por ano</h3>
                    <StackedBarChart
                      data={(projetos.pesquisa_extensao_por_ano as Record<string, Record<string, number>>) || {}}
                      keys={["pesquisa", "extensao"]}
                    />
                  </div>
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-900 mb-3">Por território</h3>
                    <SimpleBarChart
                      data={(projetos.projetos_por_territorio as Record<string, number>) || {}}
                      color="#10b981"
                    />
                  </div>
                </div>
                {(projetos.tabela_relatorios as Array<Record<string, unknown>>)?.length > 0 && (
                  <div className="glow-card rounded-xl overflow-x-auto">
                    <h3 className="text-sm font-semibold text-slate-900 p-4 border-b border-slate-200">
                      Relatórios complementares (impacto / extensão)
                    </h3>
                    <table className="w-full text-xs min-w-[800px]">
                      <thead className="bg-slate-100 text-slate-600 text-[10px] uppercase">
                        <tr>
                          <th className="p-2 text-left">Título</th>
                          <th className="p-2">Docente</th>
                          <th className="p-2">Tema</th>
                          <th className="p-2">Público</th>
                          <th className="p-2">Território</th>
                          <th className="p-2">Financ.</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(projetos.tabela_relatorios as Array<Record<string, unknown>>).map((row, i) => (
                          <tr key={i} className="border-t border-slate-200">
                            <td className="p-2 text-slate-900">{String(row.titulo)}</td>
                            <td className="p-2 text-slate-900 font-medium">{String(row.docente)}</td>
                            <td className="p-2 text-slate-600">{String(row.tema ?? "—")}</td>
                            <td className="p-2 text-slate-600">{String(row.publico ?? "—")}</td>
                            <td className="p-2">{String(row.territorio ?? "—")}</td>
                            <td className="p-2 text-center">{String(row.financiamento)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            )}

            {tab === "financiamento" && fin && (
              <section className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <KpiCard label="Confirmados" value={fin.total_financiamentos_confirmados ?? 0} accent="emerald" />
                  <KpiCard label="Mencionados (Lattes)" value={fin.total_financiamentos_mencionados ?? 0} />
                  <KpiCard label="Valor aprovado" value={fmtBRL(fin.valor_total_aprovado ?? 0)} accent="emerald" />
                  <KpiCard label="Valor executado" value={fmtBRL(fin.valor_total_executado ?? 0)} />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <ChartPanel
                    title="Por agência (R$ aprovado)"
                    exportSpec={{
                      kind: "bar",
                      title: "Financiamento por agência",
                      data: (fin.financiamentos_por_agencia as Record<string, number>) || {},
                      color: "#10b981",
                    }}
                  >
                    <SimpleBarChart
                      data={fin.financiamentos_por_agencia || {}}
                      valueFormat={fmtBRL}
                      color="#10b981"
                    />
                  </ChartPanel>
                  <ChartPanel
                    title="Mencionado vs confirmado"
                    exportSpec={{
                      kind: "bar",
                      title: "Financiamento mencionado vs confirmado",
                      data: {
                        Mencionados: fin.comparativo?.mencionados ?? 0,
                        Confirmados: fin.comparativo?.confirmados ?? 0,
                      },
                      color: "#f59e0b",
                    }}
                  >
                    <SimpleBarChart
                      data={{
                        Mencionados: fin.comparativo?.mencionados ?? 0,
                        Confirmados: fin.comparativo?.confirmados ?? 0,
                      }}
                      color="#f59e0b"
                    />
                  </ChartPanel>
                </div>
                {fin.financiamentos_por_ano &&
                  Object.keys(fin.financiamentos_por_ano as object).length > 0 && (
                    <ChartPanel
                      title="Valor aprovado por ano"
                      exportSpec={{
                        kind: "line",
                        title: "Financiamento por ano",
                        data: fin.financiamentos_por_ano as Record<string, number>,
                        color: "#10b981",
                      }}
                    >
                      <SimpleLineChart
                        data={fin.financiamentos_por_ano as Record<string, number>}
                        color="#10b981"
                      />
                    </ChartPanel>
                  )}
                <div className="glow-card rounded-xl overflow-x-auto max-h-[400px]">
                  <table className="w-full text-xs min-w-[800px]">
                    <thead className="sticky top-0 bg-slate-100 text-slate-600 text-[10px] uppercase">
                      <tr>
                        <th className="p-2 text-left">Agência</th>
                        <th className="p-2">Ano</th>
                        <th className="p-2 text-left">Docente</th>
                        <th className="p-2 text-left">Vínculo</th>
                        <th className="p-2">Origem</th>
                        <th className="p-2 text-right">Aprovado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(fin.matriz_fomento || []).slice(0, 50).map((row, i) => (
                        <tr key={i} className="border-t border-slate-200">
                          <td className="p-2 text-slate-700">{String(row.agencia ?? "—")}</td>
                          <td className="p-2 text-center text-slate-700">{String(row.ano ?? "—")}</td>
                          <td className="p-2 text-slate-900 font-medium">{String(row.docente ?? "")}</td>
                          <td className="p-2 text-slate-600 max-w-[200px] truncate">{String(row.vinculo ?? "")}</td>
                          <td className="p-2 text-center">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[9px] ${
                                row.origem === "confirmado"
                                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                  : "bg-amber-50 text-amber-700 border border-amber-200"
                              }`}
                            >
                              {String(row.origem)}
                            </span>
                          </td>
                          <td className="p-2 text-right">
                            {row.valor_aprovado != null ? fmtBRL(Number(row.valor_aprovado)) : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {tab === "eventos" && eventos && (
              <section className="space-y-6">
                <CatalogPanel kind="eventos-institucionais" onImported={loadData} />
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <KpiCard label="Total eventos" value={(eventos.total_eventos as number) ?? 0} />
                  <KpiCard
                    label="Institucionais"
                    value={(eventos.eventos_institucionais_count as number) ?? 0}
                    accent="purple"
                  />
                  <KpiCard
                    label="Inscritos (prog.)"
                    value={(eventos.total_inscritos_institucionais as number) ?? 0}
                  />
                  <KpiCard label="Trabalhos apresentados" value={(eventos.total_trabalhos_institucionais as number) ?? 0} />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-900 mb-3">Lattes — por ano</h3>
                    <SimpleLineChart data={(eventos.eventos_por_ano as Record<string, number>) || {}} color="#a855f7" />
                  </div>
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-900 mb-3">Inscritos por edição (SIMCOM…)</h3>
                    <SimpleBarChart
                      data={(eventos.inscritos_por_edicao as Record<string, number>) || {}}
                      color="#a855f7"
                    />
                  </div>
                </div>
                {(eventos.eventos_institucionais_tabela as Array<Record<string, unknown>>)?.length > 0 && (
                  <div className="glow-card rounded-xl overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead className="bg-slate-100 text-slate-600 text-[10px] uppercase">
                        <tr>
                          <th className="p-2 text-left">Evento</th>
                          <th className="p-2">Edição</th>
                          <th className="p-2">Ano</th>
                          <th className="p-2 text-right">Inscritos</th>
                          <th className="p-2 text-right">Trabalhos</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(eventos.eventos_institucionais_tabela as Array<Record<string, unknown>>).map(
                          (row, i) => (
                            <tr key={i} className="border-t border-slate-200">
                              <td className="p-2 text-slate-900">{String(row.nome)}</td>
                              <td className="p-2 text-center text-slate-600">{String(row.edicao ?? "—")}</td>
                              <td className="p-2 text-center text-slate-600">{String(row.ano ?? "—")}</td>
                              <td className="p-2 text-right text-slate-700">{String(row.inscritos ?? "—")}</td>
                              <td className="p-2 text-right text-slate-700">{String(row.trabalhos ?? "—")}</td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            )}

            {tab === "egressos" && egressos && (
              <section className="space-y-6">
                <CatalogPanel kind="egressos" onImported={loadData} />
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <KpiCard label="Total egressos" value={(egressos.total_egressos as number) ?? 0} />
                  <KpiCard label="Em doutorado" value={(egressos.egressos_em_doutorado as number) ?? 0} accent="indigo" />
                  <KpiCard label="Ensino superior" value={(egressos.egressos_ensino_superior as number) ?? 0} />
                  <KpiCard label="Municípios" value={(egressos.municipios_alcancados as number) ?? 0} />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-900 mb-3">Por ano de conclusão</h3>
                    <SimpleBarChart data={(egressos.egressos_por_ano as Record<string, number>) || {}} />
                  </div>
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-900 mb-3">Por setor</h3>
                    <SimpleBarChart data={(egressos.egressos_por_setor as Record<string, number>) || {}} color="#10b981" />
                  </div>
                </div>
                <CatalogPanel kind="processos-seletivos" onImported={loadData} />
                {demanda && (
                  <div className="glow-card rounded-xl p-5 space-y-3">
                    <h3 className="text-sm font-semibold text-slate-900">Demanda discente (seleção)</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                      <div>
                        <span className="text-slate-500">Relação candidato/vaga</span>
                        <p className="text-lg font-bold text-slate-900">{demanda.relacao_media_candidato_vaga as number}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Taxa aprovação</span>
                        <p className="text-lg font-bold text-slate-900">
                          {((demanda.taxa_aprovacao as number) * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-500">Taxa matrícula</span>
                        <p className="text-lg font-bold text-slate-900">
                          {((demanda.taxa_matricula as number) * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </section>
            )}

            {tab === "lacunas" && lac && (
              <section className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <KpiCard label="Abertas" value={lac.lacunas_abertas ?? 0} accent="amber" />
                  <KpiCard label="Críticas" value={lac.lacunas_criticas ?? 0} accent="rose" />
                  <KpiCard label="Resolvidas" value={lac.lacunas_resolvidas ?? 0} accent="emerald" />
                  <KpiCard label="Total" value={(lac.total_lacunas as number) ?? 0} />
                  <KpiCard label="Checklist APCN" value={(lac.lacunas_virtuais as number) ?? 0} accent="rose" />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-900 mb-3">Por tipo</h3>
                    <SimpleBarChart data={lac.lacunas_por_tipo || {}} color="#f59e0b" />
                  </div>
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-900 mb-3">Por seção do documento</h3>
                    <SimpleBarChart data={(lac.lacunas_por_secao as Record<string, number>) || {}} color="#ef4444" />
                  </div>
                </div>
                <div className="glow-card rounded-xl overflow-x-auto max-h-[360px]">
                  <table className="w-full text-xs min-w-[700px]">
                    <thead className="bg-slate-100 text-slate-600 text-[10px] uppercase sticky top-0">
                      <tr>
                        <th className="p-2 text-left">Tipo</th>
                        <th className="p-2 text-left">Seção</th>
                        <th className="p-2 text-left">Descrição</th>
                        <th className="p-2">Gravidade</th>
                        <th className="p-2">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(lac.tabela || []).slice(0, 80).map((row, i) => (
                        <tr key={i} className="border-t border-slate-200">
                          <td className="p-2 font-mono text-[10px] text-slate-700">{String(row.tipo_lacuna ?? row.tipo)}</td>
                          <td className="p-2 text-slate-600">{String(row.secao_documento ?? "—")}</td>
                          <td className="p-2 text-slate-800 max-w-xs truncate" title={String(row.descricao)}>
                            {String(row.descricao)}
                          </td>
                          <td className="p-2 text-center">{String(row.gravidade)}</td>
                          <td className="p-2 text-center">
                            {row.resolvido ? (
                              <span className="text-emerald-400">OK</span>
                            ) : row.virtual ? (
                              <span className="text-rose-400" title={String(row.sugestao_de_correcao || "")}>
                                APCN
                              </span>
                            ) : row.id ? (
                              <button
                                type="button"
                                className="text-[10px] px-2 py-0.5 bg-emerald-600 rounded text-white hover:bg-emerald-500"
                                onClick={async () => {
                                  await apiFetch(`/lacunas/${row.id}`, {
                                    method: "PATCH",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ resolvido: true }),
                                  });
                                  loadData();
                                }}
                              >
                                Resolver
                              </button>
                            ) : (
                              <span className="text-amber-400">Aberta</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {tab === "exportacoes" && (
              <section className="glow-card rounded-xl p-8 space-y-6">
                <h3 className="text-lg font-semibold text-slate-900">Exportações</h3>
                <p className="text-sm text-slate-600">
                  Baixe CSVs, gráficos PNG e o resumo em Markdown para colar na proposta de doutorado.
                </p>
                <ExportButtons query={buildDossieQuery(filters)} />
                <div className="pt-4 border-t border-slate-200 space-y-2">
                  <p className="text-[10px] text-slate-500 uppercase font-bold">Gráficos PNG (filtros atuais)</p>
                  <div className="flex flex-wrap gap-2">
                    {producao?.producao_por_ano &&
                      Object.keys(producao.producao_por_ano as object).length > 0 && (
                        <button
                          type="button"
                          className="px-3 py-2 btn-secondary rounded-lg text-xs hover:border-indigo-400"
                          onClick={() =>
                            downloadChartPng({
                              kind: "line",
                              title: "Produção por ano",
                              data: producao.producao_por_ano as Record<string, number>,
                            })
                          }
                        >
                          producao_por_ano.png
                        </button>
                      )}
                    {financiamento?.financiamentos_por_agencia &&
                      Object.keys(financiamento.financiamentos_por_agencia as object).length > 0 && (
                        <button
                          type="button"
                          className="px-3 py-2 btn-secondary rounded-lg text-xs hover:border-indigo-400"
                          onClick={() =>
                            downloadChartPng({
                              kind: "bar",
                              title: "Financiamento por agência",
                              data: financiamento.financiamentos_por_agencia as Record<string, number>,
                              color: "#10b981",
                            })
                          }
                        >
                          financiamento_agencia.png
                        </button>
                      )}
                    {lacunas?.lacunas_por_tipo &&
                      Object.keys(lacunas.lacunas_por_tipo as object).length > 0 && (
                        <button
                          type="button"
                          className="px-3 py-2 btn-secondary rounded-lg text-xs hover:border-indigo-400"
                          onClick={() =>
                            downloadChartPng({
                              kind: "bar",
                              title: "Lacunas por tipo",
                              data: lacunas.lacunas_por_tipo as Record<string, number>,
                              color: "#f59e0b",
                            })
                          }
                        >
                          lacunas_tipo.png
                        </button>
                      )}
                  </div>
                  <p className="text-[10px] text-slate-500">
                    Também disponível o botão PNG em cada gráfico nas abas do dossiê.
                  </p>
                </div>
                {narrativas && (
                  <div className="space-y-4 pt-4 border-t border-slate-200">
                    <div className="flex items-center justify-between gap-4">
                      <h4 className="text-sm font-semibold text-slate-900">Textos-síntese (narrativas)</h4>
                      <button
                        type="button"
                        className="text-xs px-3 py-1.5 btn-secondary rounded-lg hover:border-indigo-400"
                        onClick={() => {
                          const text = Object.entries(narrativas)
                            .map(([k, v]) => `## ${k}\n\n${v}`)
                            .join("\n\n");
                          navigator.clipboard.writeText(text);
                        }}
                      >
                        Copiar textos
                      </button>
                    </div>
                    {Object.entries(narrativas).map(([key, text]) => (
                      <div key={key} className="text-xs text-slate-600 leading-relaxed">
                        <span className="text-indigo-600 font-bold uppercase block mb-1">{key}</span>
                        {text}
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}
