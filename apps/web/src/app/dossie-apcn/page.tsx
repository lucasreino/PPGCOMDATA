"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
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
import { KpiCard, SimpleBarChart, SimpleLineChart } from "@/components/dossie/charts";

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

  const loadData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    const q = buildDossieQuery(filters);
    try {
      const [ov, co, pr, pj, fi, ev, la] = await Promise.all([
        apiFetch(`/dossie-apcn/overview${q}`),
        apiFetch(`/dossie-apcn/corpo-docente${q}`),
        apiFetch(`/dossie-apcn/producao${q}`),
        apiFetch(`/dossie-apcn/projetos${q}`),
        apiFetch(`/dossie-apcn/financiamento${q}`),
        apiFetch(`/dossie-apcn/eventos${q}`),
        apiFetch(`/dossie-apcn/lacunas${q}`),
      ]);
      const parse = async (res: Response, name: string) => {
        if (!res.ok) throw new Error(`Falha ao carregar ${name}`);
        return res.json();
      };
      setOverview(await parse(ov, "visão geral"));
      setCorpo(await parse(co, "corpo docente"));
      setProducao(await parse(pr, "produção"));
      setProjetos(await parse(pj, "projetos"));
      setFinanciamento(await parse(fi, "financiamento"));
      setEventos(await parse(ev, "eventos"));
      setLacunas(await parse(la, "lacunas"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar indicadores");
    } finally {
      setLoading(false);
    }
  }, [user, filters]);

  useEffect(() => {
    if (user) loadData();
  }, [user, loadData]);

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-400 text-sm">
        Carregando sessão...
      </div>
    );
  }

  const ov = overview as {
    total_docentes?: number;
    total_producoes?: number;
    total_projetos?: number;
    total_eventos?: number;
    fomento_total?: { aprovado: number };
    lacunas_pendentes?: number;
    validacao_pendentes?: number;
    total_orientacoes?: number;
    modulos_disponiveis?: Record<string, boolean>;
  } | null;

  const prod = producao as {
    totais?: Record<string, number>;
    producao_por_ano?: Record<string, number>;
    producao_por_docente?: Record<string, number>;
    producao_por_tipo?: Record<string, number>;
    tabela_por_docente?: Array<Record<string, string | number>>;
  } | null;

  const fin = financiamento as {
    total_financiamentos_confirmados?: number;
    total_financiamentos_mencionados?: number;
    valor_total_aprovado?: number;
    valor_total_executado?: number;
    financiamentos_por_agencia?: Record<string, number>;
    financiamentos_por_ano?: Record<string, number>;
    comparativo?: { mencionados: number; confirmados: number };
    matriz_fomento?: Array<Record<string, unknown>>;
  } | null;

  const lac = lacunas as {
    lacunas_abertas?: number;
    lacunas_criticas?: number;
    lacunas_resolvidas?: number;
    lacunas_por_tipo?: Record<string, number>;
    lacunas_por_docente?: Record<string, number>;
    lacunas_por_gravidade?: Record<string, number>;
    tabela?: Array<Record<string, unknown>>;
  } | null;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-[#1e293b] bg-[#0f172a]/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-2 rounded-lg border border-slate-800 text-slate-400 hover:text-white hover:border-slate-600"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="bg-indigo-600 p-2 rounded-lg text-white">
              <BarChart2 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Dossiê APCN</h1>
              <p className="text-xs text-slate-400">Proposta de Doutorado — PPGCOM</p>
            </div>
          </div>
          <span className="text-[10px] px-3 py-1 rounded-full bg-indigo-950 border border-indigo-800 text-indigo-300">
            Dados reais do banco
          </span>
        </div>
        <div className="flex flex-wrap gap-1 mt-4 overflow-x-auto pb-1">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setTab(id)}
              className={`px-3 py-2 rounded-lg text-[11px] font-bold whitespace-nowrap flex items-center gap-1.5 transition-all ${
                tab === id
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-slate-200 bg-slate-950 border border-slate-800"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>
      </header>

      <main className="flex-1 p-6 space-y-6 max-w-[1400px] mx-auto w-full">
        <DossieFiltersBar
          filters={filters}
          onChange={setFilters}
          onRefresh={loadData}
          loading={loading}
          professores={professores}
          linhas={linhas}
        />

        {error && (
          <div className="rounded-lg border border-rose-800 bg-rose-950/40 text-rose-300 text-sm px-4 py-3">
            {error}
          </div>
        )}

        {loading && !overview ? (
          <div className="text-center py-20 text-slate-400 text-sm">Carregando indicadores...</div>
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
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-4">Produção por ano</h3>
                    <SimpleLineChart data={prod.producao_por_ano} />
                  </div>
                )}
                <p className="text-xs text-slate-500">
                  Módulos em breve: egressos e processos seletivos (Etapas 7–8 da proposta).
                </p>
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
                    <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px]">
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
                        <tr key={String(row.id)} className="border-t border-slate-800/80 hover:bg-slate-900/40">
                          <td className="p-3 text-slate-200">{String(row.nome)}</td>
                          <td className="p-3 text-slate-400">{String(row.linha)}</td>
                          <td className="p-3 text-right text-indigo-300">{String(row.producoes)}</td>
                          <td className="p-3 text-right">{String(row.projetos)}</td>
                          <td className="p-3 text-right text-amber-400">{String(row.lacunas_abertas)}</td>
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
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">Por docente</h3>
                    <SimpleBarChart data={prod.producao_por_docente || {}} />
                  </div>
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">Por tipo</h3>
                    <SimpleBarChart data={prod.producao_por_tipo || {}} color="#a855f7" />
                  </div>
                </div>
                <div className="glow-card rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-slate-300 mb-3">Evolução por ano</h3>
                  <SimpleLineChart data={prod.producao_por_ano || {}} />
                </div>
                <div className="glow-card rounded-xl overflow-x-auto">
                  <table className="w-full text-xs min-w-[700px]">
                    <thead className="bg-slate-900/80 text-slate-400 text-[10px] uppercase">
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
                        <tr key={String(row.professor_id)} className="border-t border-slate-800">
                          <td className="p-3">{String(row.docente)}</td>
                          <td className="p-3 text-slate-400">{String(row.linha)}</td>
                          <td className="p-3 text-right">{row.artigos}</td>
                          <td className="p-3 text-right">{row.livros}</td>
                          <td className="p-3 text-right">{row.capitulos}</td>
                          <td className="p-3 text-right">{row.anais}</td>
                          <td className="p-3 text-right">{row.producao_tecnica}</td>
                          <td className="p-3 text-right font-bold text-indigo-300">{row.total}</td>
                          <td className="p-3 text-right text-amber-400">{row.pendencias}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {tab === "projetos" && projetos && (
              <section className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <KpiCard label="Pesquisa" value={(projetos.total_projetos_pesquisa as number) ?? 0} />
                  <KpiCard label="Extensão" value={(projetos.total_projetos_extensao as number) ?? 0} accent="emerald" />
                  <KpiCard label="Com financiamento" value={(projetos.projetos_com_financiamento as number) ?? 0} />
                  <KpiCard label="Relatórios complementares" value={(projetos.total_relatorios_complementares as number) ?? 0} />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">Por docente</h3>
                    <SimpleBarChart data={(projetos.projetos_por_docente as Record<string, number>) || {}} color="#10b981" />
                  </div>
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">Por ano</h3>
                    <SimpleLineChart data={(projetos.projetos_por_ano as Record<string, number>) || {}} color="#10b981" />
                  </div>
                </div>
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
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">Por agência (R$ aprovado)</h3>
                    <SimpleBarChart
                      data={fin.financiamentos_por_agencia || {}}
                      valueFormat={fmtBRL}
                      color="#10b981"
                    />
                  </div>
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">Mencionado vs confirmado</h3>
                    <SimpleBarChart
                      data={{
                        Mencionados: fin.comparativo?.mencionados ?? 0,
                        Confirmados: fin.comparativo?.confirmados ?? 0,
                      }}
                      color="#f59e0b"
                    />
                  </div>
                </div>
                <div className="glow-card rounded-xl overflow-x-auto max-h-[400px]">
                  <table className="w-full text-xs min-w-[800px]">
                    <thead className="sticky top-0 bg-slate-900 text-slate-400 text-[10px] uppercase">
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
                        <tr key={i} className="border-t border-slate-800">
                          <td className="p-2">{String(row.agencia ?? "—")}</td>
                          <td className="p-2 text-center">{String(row.ano ?? "—")}</td>
                          <td className="p-2">{String(row.docente ?? "")}</td>
                          <td className="p-2 text-slate-400 max-w-[200px] truncate">{String(row.vinculo ?? "")}</td>
                          <td className="p-2 text-center">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[9px] ${
                                row.origem === "confirmado"
                                  ? "bg-emerald-950 text-emerald-400"
                                  : "bg-amber-950 text-amber-400"
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
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <KpiCard label="Total eventos" value={(eventos.total_eventos as number) ?? 0} />
                  <KpiCard label="Organizados" value={(eventos.eventos_organizados as number) ?? 0} accent="purple" />
                  <KpiCard label="Nacionais" value={(eventos.eventos_nacionais as number) ?? 0} />
                  <KpiCard label="Internacionais" value={(eventos.eventos_internacionais as number) ?? 0} />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">Por ano</h3>
                    <SimpleLineChart data={(eventos.eventos_por_ano as Record<string, number>) || {}} color="#a855f7" />
                  </div>
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">Por docente</h3>
                    <SimpleBarChart data={(eventos.eventos_por_docente as Record<string, number>) || {}} color="#a855f7" />
                  </div>
                </div>
                <p className="text-xs text-slate-500">{String(eventos.nota || "")}</p>
              </section>
            )}

            {tab === "egressos" && (
              <section className="glow-card rounded-xl p-10 text-center space-y-3">
                <GraduationCap className="w-12 h-12 text-slate-600 mx-auto" />
                <h3 className="text-lg font-semibold text-slate-300">Egressos e impacto regional</h3>
                <p className="text-sm text-slate-500 max-w-md mx-auto">
                  Previsto na Etapa 7: cadastro de egressos + importação CSV. Os indicadores do Lattes já
                  estão disponíveis nas demais abas.
                </p>
              </section>
            )}

            {tab === "lacunas" && lac && (
              <section className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <KpiCard label="Abertas" value={lac.lacunas_abertas ?? 0} accent="amber" />
                  <KpiCard label="Críticas" value={lac.lacunas_criticas ?? 0} accent="rose" />
                  <KpiCard label="Resolvidas" value={lac.lacunas_resolvidas ?? 0} accent="emerald" />
                  <KpiCard label="Total" value={(lacunas?.total_lacunas as number) ?? 0} />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">Por tipo</h3>
                    <SimpleBarChart data={lac.lacunas_por_tipo || {}} color="#f59e0b" />
                  </div>
                  <div className="glow-card rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-slate-300 mb-3">Por docente (abertas)</h3>
                    <SimpleBarChart data={lac.lacunas_por_docente || {}} color="#ef4444" />
                  </div>
                </div>
                <div className="glow-card rounded-xl overflow-x-auto max-h-[360px]">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-900 text-slate-400 text-[10px] uppercase sticky top-0">
                      <tr>
                        <th className="p-2 text-left">Tipo</th>
                        <th className="p-2 text-left">Descrição</th>
                        <th className="p-2">Gravidade</th>
                        <th className="p-2">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(lac.tabela || []).slice(0, 80).map((row, i) => (
                        <tr key={i} className="border-t border-slate-800">
                          <td className="p-2 font-mono text-[10px]">{String(row.tipo)}</td>
                          <td className="p-2 text-slate-300">{String(row.descricao)}</td>
                          <td className="p-2 text-center">{String(row.gravidade)}</td>
                          <td className="p-2 text-center">
                            {row.resolvido ? (
                              <span className="text-emerald-400">OK</span>
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
              <section className="glow-card rounded-xl p-8 space-y-4">
                <h3 className="text-lg font-semibold text-white">Exportações</h3>
                <p className="text-sm text-slate-400">
                  Etapa 10 da proposta: CSV, Markdown e PNG. Enquanto isso, use os dados desta tela e a aba
                  &quot;Gerar Relatório com IA&quot; na página principal.
                </p>
                <ul className="text-xs text-slate-500 space-y-1 list-disc list-inside">
                  <li>GET /dossie-apcn/producao — JSON para planilhas</li>
                  <li>GET /dossie-apcn/financiamento — matriz de fomento</li>
                  <li>GET /dossie-apcn/lacunas — checklist de evidências</li>
                </ul>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}
