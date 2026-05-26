// @ts-nocheck — view extraída do dashboard legado; tipagem incremental na fase 2
"use client";

import React from "react";
import { BarChart2, Award, Check, FileText, RefreshCw } from "lucide-react";
import { SimpleMarkdownRenderer } from "@/components/ui/validation-ui";
import { useDashboard } from "../DashboardProvider";

export function RelatoriosView() {
  const d = useDashboard();
  return (
        <main className="report-print-layout flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 py-6 animate-fadeIn">
          
          {/* Lado Esquerdo: Configuração da Geração (4 colunas) */}
          <div className="no-print lg:col-span-4 space-y-6">
            <div className="glow-card rounded-xl p-5 space-y-5 border border-slate-200">
              <div className="flex items-center space-x-2 border-b border-slate-200 pb-3">
                <BarChart2 className="w-5 h-5 text-indigo-400 animate-pulse" />
                <h2 className="text-sm font-bold tracking-wider text-slate-300 uppercase">Configurar Relatório</h2>
              </div>

              {/* Filtros Contextuais */}
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Docente Alvo</label>
                  <select
                    value={d.reportProfessorId}
                    onChange={(e) => d.setReportProfessorId(e.target.value)}
                    className="input-field text-xs"
                  >
                    <option value="todos">Todos os Docentes (Geral)</option>
                    {d.professors.map((p) => (
                      <option key={p.id} value={p.id}>{p.nome_completo}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Linha de Pesquisa</label>
                  <select
                    value={d.reportLinhaPesquisaId}
                    onChange={(e) => d.setReportLinhaPesquisaId(e.target.value)}
                    className="input-field text-xs"
                  >
                    <option value="todas">Todas as Linhas</option>
                    {d.linhasPesquisa.map((l) => (
                      <option key={l.id} value={l.id}>{l.nome}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Início</label>
                    <input
                      type="number"
                      value={d.reportAnoInicio}
                      onChange={(e) => d.setReportAnoInicio(e.target.value)}
                      className="input-field text-xs"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Fim</label>
                    <input
                      type="number"
                      value={d.reportAnoFim}
                      onChange={(e) => d.setReportAnoFim(e.target.value)}
                      className="input-field text-xs"
                    />
                  </div>
                </div>
              </div>

              {/* Templates Rápidos */}
              <div className="space-y-2.5 pt-2 border-t border-slate-200">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Presets e Templates Rápidos</label>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => d.setReportPrompt("Gere um relatório abrangente contendo o balanço de fomento recebido (CNPq, CAPES, FAPEMA), discriminando os valores por agência e o percentual de captação de cada docente.")}
                    className="w-full text-left p-2 bg-slate-50 border border-slate-200 hover:border-indigo-900 rounded text-[10.5px] text-slate-400 hover:text-indigo-300 font-medium transition-colors"
                  >
                    💰 Balanço de Fomento & Captação
                  </button>
                  <button
                    onClick={() => d.setReportPrompt("Redija uma síntese acadêmica detalhada das produções, destacando os artigos de periódicos mais relevantes e a aderência deles à linha de pesquisa correspondente.")}
                    className="w-full text-left p-2 bg-slate-50 border border-slate-200 hover:border-indigo-900 rounded text-[10.5px] text-slate-400 hover:text-indigo-300 font-medium transition-colors"
                  >
                    📚 Síntese de Periódicos & Publicações
                  </button>
                  <button
                    onClick={() => d.setReportPrompt("Gere um sumário executivo focado nos alertas e gaps de informação nos currículos. Explique quais são as principais inconsistências encontradas e forneça recomendações para a coordenação resolvê-las.")}
                    className="w-full text-left p-2 bg-slate-50 border border-slate-200 hover:border-indigo-900 rounded text-[10.5px] text-slate-400 hover:text-indigo-300 font-medium transition-colors"
                  >
                    ⚠️ Sumário Executivo de Gaps/Incoerências
                  </button>
                </div>
              </div>

              {/* Instruções do Coordenador */}
              <div className="space-y-2 pt-2 border-t border-slate-200">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">O que você precisa focar no relatório?</label>
                <textarea
                  rows={4}
                  value={d.reportPrompt}
                  onChange={(e) => d.setReportPrompt(e.target.value)}
                  placeholder="Ex: Faça uma análise comparativa do fomento ativo e o volume de publicações recentes em periódicos..."
                  className="w-full bg-slate-50 border border-slate-800 hover:border-slate-300 focus:border-indigo-600 outline-none p-2.5 rounded text-xs text-slate-200 placeholder-slate-600 resize-none leading-relaxed"
                />
              </div>

              <button
                disabled={d.generatingReport}
                onClick={d.handleGenerateReport}
                className={`w-full py-3 px-4 rounded-xl font-bold text-xs transition-all flex items-center justify-center gap-2 ${
                  d.generatingReport
                    ? "bg-indigo-900/50 text-indigo-400 border border-indigo-850 cursor-not-allowed"
                    : "bg-indigo-600 text-white hover:bg-indigo-500 hover:scale-[1.01] shadow-lg shadow-indigo-600/20 cursor-pointer active:scale-[0.99]"
                }`}
              >
                {d.generatingReport ? (
                  <>
                    <RefreshCw className="w-4.5 h-4.5 animate-spin" />
                    Gerando Relatório com IA...
                  </>
                ) : (
                  <>
                    <Award className="w-4.5 h-4.5" />
                    Gerar Relatório Executivo
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Lado Direito: Visualizador de Markdown Executivo (8 colunas) */}
          <div className="report-print-panel lg:col-span-8 flex flex-col h-full min-h-[580px] space-y-6">
            <div className="glow-card rounded-xl p-5 flex flex-col flex-1 border border-slate-200">
              
              <div className="no-print flex justify-between items-center border-b border-slate-200 pb-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 tracking-wider uppercase">Relatório Gerado por IA</h3>
                  {d.reportModelUsed && (
                    <span className="text-[10px] text-indigo-400 font-bold font-mono block mt-0.5">
                      Modelo: {d.reportModelUsed}
                    </span>
                  )}
                </div>

                {d.reportText && !d.generatingReport && (
                  <div className="flex gap-2">
                    <button
                      onClick={d.copyToClipboard}
                      className="py-1.5 px-3 bg-slate-50 border border-slate-200 hover:border-slate-300 text-xs font-semibold text-slate-600 hover:text-slate-900 rounded-lg transition-colors flex items-center gap-1.5"
                      title="Copiar Relatório"
                    >
                      <Check className="w-3.5 h-3.5" />
                      Copiar
                    </button>
                    <button
                      onClick={d.downloadMarkdown}
                      className="py-1.5 px-3 bg-slate-50 border border-slate-200 hover:border-slate-300 text-xs font-semibold text-slate-600 hover:text-slate-900 rounded-lg transition-colors flex items-center gap-1.5"
                      title="Baixar Markdown (.md)"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      Baixar .MD
                    </button>
                    <button
                      onClick={d.handlePrintReport}
                      className="py-1.5 px-3 bg-indigo-950/60 border border-indigo-900 hover:bg-indigo-900 text-xs font-semibold text-indigo-400 hover:text-indigo-200 rounded-lg transition-all flex items-center gap-1.5"
                      title="Imprimir ou salvar como PDF (na própria página)"
                    >
                      <Award className="w-3.5 h-3.5" />
                      Imprimir PDF
                    </button>
                  </div>
                )}
              </div>

              {/* Workspace Content Area */}
              <div className="flex-1 flex flex-col justify-center mt-5 overflow-y-auto max-h-[500px] pr-1 print:max-h-none print:overflow-visible">
                {d.generatingReport ? (
                  <div className="no-print flex flex-col items-center justify-center py-20 space-y-6 text-center">
                    <div className="relative">
                      <div className="w-14 h-14 rounded-full border-4 border-indigo-950 border-t-indigo-500 animate-spin"></div>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <BarChart2 className="w-6 h-6 text-indigo-400 animate-pulse" />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <h4 className="text-sm font-bold text-slate-300">Inteligência Artificial Pensando...</h4>
                      <p className="text-xs text-slate-500 max-w-[280px] mx-auto leading-normal">
                        Estamos consolidando os indicadores e gerando o parecer analítico.
                      </p>
                    </div>

                    {/* Generation Logs Console */}
                    <div className="w-full max-w-sm bg-slate-50 border border-slate-200 rounded-lg p-3 text-left font-mono text-[10px] text-slate-400 space-y-1.5 h-28 overflow-y-auto">
                      {d.reportLogs.map((log, index) => (
                        <div key={index} className="flex gap-2">
                          <span className="text-indigo-500 font-bold select-none">&gt;</span>
                          <span className={index === d.reportLogs.length - 1 ? "text-indigo-400 animate-pulse font-semibold" : ""}>{log}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : d.reportText ? (
                  <div
                    id="report-print-root"
                    className="bg-slate-50/45 p-6 rounded-xl border border-slate-200/60 leading-relaxed text-slate-300 text-xs overflow-wrap-break text-left"
                  >
                    <div className="print-only mb-4 pb-3 border-b border-slate-300 text-slate-800 text-[10pt]">
                      <p className="font-bold text-indigo-900 text-sm">PPGCOMDATA — Relatório analítico</p>
                      <p className="mt-1 text-slate-600">
                        {d.reportProfessorId === "todos"
                          ? "Todos os docentes"
                          : d.professors.find((p) => p.id === d.reportProfessorId)?.nome_completo}
                        {" · "}
                        {d.reportAnoInicio}—{d.reportAnoFim}
                        {d.reportModelUsed ? ` · ${d.reportModelUsed}` : ""}
                      </p>
                    </div>
                    <SimpleMarkdownRenderer content={d.reportText} />
                  </div>
                ) : (
                  <div className="no-print text-center py-20 text-slate-500 text-xs space-y-3">
                    <Award className="w-12 h-12 text-slate-700 mx-auto" />
                    <p className="font-semibold text-slate-400">Pronto para gerar pareceres e sínteses analíticas!</p>
                    <p className="max-w-xs mx-auto text-slate-500 leading-normal">
                      Selecione os filtros desejados, escolha um template rápido ou redija uma orientação personalizada para iniciar o pipeline de IA.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
  );
}
