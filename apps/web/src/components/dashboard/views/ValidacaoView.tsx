// @ts-nocheck — view extraída do dashboard legado; tipagem incremental na fase 2
"use client";

import React from "react";
import {
  FileText, Upload, Check, Edit2, Trash2, AlertTriangle,
  HelpCircle, CheckCircle, RefreshCw, BarChart2, Plus,
  BookOpen, Calendar, DollarSign, Eye, EyeOff, Clock, ArrowRight, UserPlus, Info,
  Users, GraduationCap, Wrench, Trophy, Network
} from "lucide-react";
import { ResumoAcademicoCard } from "@/components/academic/ResumoAcademicoCard";
import { ProducaoIndicadores } from "@/components/academic/ProducaoIndicadores";
import {
  ActionPanel, ConfidenceBadge, EmptyState, OriginalFragment,
} from "@/components/ui/validation-ui";
import type { EntityTab } from "@/lib/types";
import { useDashboard } from "../DashboardProvider";

export function ValidacaoView() {
  const d = useDashboard();
  return (
        <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 py-6 animate-fadeIn">
        
        {/* Left Side: Professor Selection & Lattes Upload (3 Cols) */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* Professors Card */}
          <div className="glow-card rounded-xl p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-sm font-semibold tracking-wider text-slate-600 uppercase">Corpo Docente</h2>
              <span className="text-xs px-2 py-0.5 bg-slate-100 rounded text-slate-400 font-semibold">{d.professors.length}</span>
            </div>
            
            <div className="space-y-3">
              {d.professors.map((p) => {
                const isSelected = p.id === d.selectedProfId;
                return (
                  <button
                    key={p.id}
                    onClick={() => d.setSelectedProfId(p.id)}
                    className={`w-full text-left p-3 rounded-lg border transition-all duration-200 flex flex-col ${
                      isSelected 
                        ? "bg-indigo-50 border-indigo-300 shadow-sm" 
                        : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center justify-between w-full">
                      <span className="font-semibold text-sm text-slate-900">{p.nome_completo}</span>
                      <span className={`w-2 h-2 rounded-full ${
                        p.status === "validado" ? "bg-emerald-500" : p.status === "processado" ? "bg-blue-500 animate-pulse" : "bg-amber-500"
                      }`}></span>
                    </div>
                    <span className="text-xs text-slate-400 mt-1">{p.linha}</span>
                    
                    <div className="flex justify-between items-center w-full mt-2.5 pt-2 border-t border-slate-200 text-[10px]">
                      <span className="text-slate-500 font-medium">{p.tipo}</span>
                      <span className={`px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                        p.status === "validado" 
                          ? "bg-emerald-50 text-emerald-800 border border-emerald-200" 
                          : p.status === "processado" 
                          ? "bg-blue-50 text-blue-800 border border-blue-200"
                          : "bg-amber-50 text-amber-800 border border-amber-200"
                      }`}>
                        {p.status}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              onClick={() => d.setShowNovoDocenteModal(true)}
              disabled={!d.apiConnected}
              title={d.apiConnected ? "Cadastrar novo docente" : "Conecte-se à API para cadastrar"}
              className="w-full mt-4 flex items-center justify-center gap-2 py-2 px-3 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-xs font-semibold text-indigo-700 transition-colors"
            >
              <UserPlus className="w-4.5 h-4.5" />
              Novo Docente
            </button>
          </div>

          {/* Lattes import (HTML → XML ou XML direto) */}
          <div className="glow-card rounded-xl p-5">
            <h2 className="text-sm font-semibold tracking-wider text-slate-600 uppercase mb-4">
              Importar Lattes
            </h2>

            <div className="space-y-4">
              <div className="flex rounded-lg border border-slate-200 p-0.5 bg-slate-50">
                <button
                  type="button"
                  onClick={() => d.handleLattesFonteChange("html")}
                  className={`flex-1 py-1.5 text-[10px] font-bold rounded-md transition-colors ${
                    d.lattesFonte === "html"
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  HTML → XML
                </button>
                <button
                  type="button"
                  onClick={() => d.handleLattesFonteChange("xml")}
                  className={`flex-1 py-1.5 text-[10px] font-bold rounded-md transition-colors ${
                    d.lattesFonte === "xml"
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  XML direto
                </button>
              </div>

              <div
                onClick={() => d.fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-300 hover:border-indigo-400 hover:bg-indigo-50 rounded-xl p-6 text-center cursor-pointer transition-all duration-200"
              >
                <input
                  type="file"
                  ref={d.fileInputRef}
                  onChange={d.handleFileChange}
                  accept={d.lattesFonte === "html" ? ".html,.htm" : ".xml"}
                  className="hidden"
                />
                <Upload className="w-8 h-8 text-indigo-500 mx-auto mb-3" />
                <span className="text-xs font-semibold text-slate-700 block mb-1">
                  {d.selectedFile
                    ? d.selectedFile.name
                    : d.lattesFonte === "html"
                      ? "Selecionar HTML salvo do Lattes"
                      : "Selecionar arquivo XML"}
                </span>
                <span className="text-[10px] text-slate-500 block leading-relaxed">
                  {d.lattesFonte === "html"
                    ? "No Lattes: menu → Salvar currículo em HTML. O sistema converte para XML (lattes-xml)."
                    : "Use o XML exportado do Lattes, se você já tiver o arquivo."}
                </span>
              </div>

              {d.isProcessing && (
                <div className="space-y-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-indigo-600 font-semibold">{d.processingStep}</span>
                    <span className="text-slate-600 font-bold">{d.uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-indigo-600 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${d.uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              <button
                disabled={!d.selectedFile || d.isProcessing || !d.selectedProfId}
                onClick={d.handleUploadAndProcess}
                className={`w-full py-2.5 px-4 rounded-lg font-semibold text-xs transition-all flex items-center justify-center gap-2 ${
                  d.selectedFile && !d.isProcessing && d.selectedProfId
                    ? "bg-indigo-600 text-white hover:bg-indigo-500 shadow-lg shadow-indigo-600/20 cursor-pointer"
                    : "bg-slate-100 text-slate-500 cursor-not-allowed"
                }`}
              >
                {d.isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Importando...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" />
                    Importar currículo
                  </>
                )}
              </button>

              <button
                type="button"
                disabled={!d.apiConnected || d.isProcessing}
                onClick={d.handleReprocessCurriculo}
                className={`w-full py-2 px-4 rounded-lg font-semibold text-xs border transition-all flex items-center justify-center gap-2 ${
                  d.apiConnected && !d.isProcessing
                    ? "border-slate-300 text-slate-600 hover:border-indigo-400 hover:bg-indigo-50"
                    : "border-slate-200 text-slate-400 cursor-not-allowed"
                }`}
                title="Reimporta o último HTML/XML enviado deste docente"
              >
                <RefreshCw className={`w-4 h-4 ${d.isProcessing ? "animate-spin" : ""}`} />
                Reimportar último Lattes
              </button>
            </div>
          </div>
        </div>

        {/* Center Panel: Human-in-the-Loop Validation View (6 Cols) */}
        <div className="lg:col-span-6 space-y-6">

          <ResumoAcademicoCard resumo={d.resumoAcademico} />
          
          {/* Tabs navigation */}
          <div className="bg-white p-1 border border-slate-200 shadow-sm rounded-xl flex flex-wrap gap-1">
            {d.VALIDATION_TABS.map((tab) => {
              const count =
                tab === "projetos" ? d.projetos.length
                : tab === "eventos" ? d.eventos.length
                : tab === "producoes" ? d.producoes.length
                : tab === "financiamentos" ? d.financiamentos.length
                : tab === "orientacoes" ? d.orientacoes.length
                : tab === "formacoes_academicas" ? d.formacoes.length
                : tab === "producoes_tecnicas" ? d.producoesTecnicas.length
                : tab === "premios" ? d.premios.length
                : d.gruposPesquisa.length;

              return (
                <button
                  key={tab}
                  onClick={() => d.setActiveTab(tab)}
                  className={`flex-1 min-w-[88px] py-2 px-2 text-[11px] font-semibold rounded-lg transition-all duration-200 flex items-center justify-center gap-1.5 ${
                    d.activeTab === tab
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/10"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {tab === "projetos" && <BookOpen className="w-3.5 h-3.5" />}
                  {tab === "eventos" && <Calendar className="w-3.5 h-3.5" />}
                  {tab === "producoes" && <FileText className="w-3.5 h-3.5" />}
                  {tab === "financiamentos" && <DollarSign className="w-3.5 h-3.5" />}
                  {tab === "orientacoes" && <Users className="w-3.5 h-3.5" />}
                  {tab === "formacoes_academicas" && <GraduationCap className="w-3.5 h-3.5" />}
                  {tab === "producoes_tecnicas" && <Wrench className="w-3.5 h-3.5" />}
                  {tab === "premios" && <Trophy className="w-3.5 h-3.5" />}
                  {tab === "grupos_pesquisa" && <Network className="w-3.5 h-3.5" />}
                  {d.tabLabel(tab)}
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                    d.activeTab === tab ? "bg-indigo-500 text-white" : "bg-slate-100 text-slate-400"
                  }`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Validation workspace */}
          <div className="space-y-4">
            
            {/* Empty State */}
            {d.activeTab === "projetos" && d.projetos.length === 0 && <EmptyState tab="projetos" />}
            {d.activeTab === "eventos" && d.eventos.length === 0 && <EmptyState tab="eventos" />}
            {d.activeTab === "producoes" && d.producoes.length === 0 && <EmptyState tab="producoes" />}
            {d.activeTab === "financiamentos" && d.financiamentos.length === 0 && <EmptyState tab="financiamentos" />}
            {d.activeTab === "orientacoes" && d.orientacoes.length === 0 && <EmptyState tab="orientacoes" />}
            {d.activeTab === "formacoes_academicas" && d.formacoes.length === 0 && <EmptyState tab="formacoes_academicas" />}
            {d.activeTab === "producoes_tecnicas" && d.producoesTecnicas.length === 0 && <EmptyState tab="produções técnicas" />}
            {d.activeTab === "premios" && d.premios.length === 0 && <EmptyState tab="prêmios" />}
            {d.activeTab === "grupos_pesquisa" && d.gruposPesquisa.length === 0 && <EmptyState tab="grupos de pesquisa" />}

            {/* PROJECTS VIEW */}
            {d.activeTab === "projetos" && d.projetos.map((item) => (
              <div 
                key={item.id} 
                className={`glow-card rounded-xl p-5 border transition-all duration-300 relative overflow-hidden ${
                  item.status_validacao === "confirmado" ? "border-emerald-300 bg-emerald-50" :
                  item.status_validacao === "editado" ? "border-indigo-300 bg-indigo-50" :
                  item.status_validacao === "descartado" ? "border-rose-200 bg-rose-50 opacity-60 hover:opacity-70" : "border-slate-200"
                }`}
              >
                {/* Visual Status Indicator tag */}
                <div className="absolute top-0 left-0 right-0 h-1 flex">
                  <div className={`w-full ${
                    item.status_validacao === "confirmado" ? "bg-emerald-500" :
                    item.status_validacao === "editado" ? "bg-indigo-500" :
                    item.status_validacao === "descartado" ? "bg-rose-500" : "bg-slate-700"
                  }`}></div>
                </div>

                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <span className="text-[10px] px-2 py-0.5 bg-slate-100 border border-slate-300 text-slate-700 rounded font-bold uppercase tracking-wider">
                      {item.tipo}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 mt-1">{item.titulo}</h3>
                  </div>

                  <ConfidenceBadge level={item.confianca_ia} />
                </div>

                <p className="text-xs text-slate-400 mt-3.5 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                  {item.descricao}
                </p>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4 text-[11px] text-slate-300">
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Vigência</span>
                    <span className="font-semibold">{item.ano_inicio} — {item.ano_fim || "Atual"}</span>
                  </div>
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Papel</span>
                    <span className="font-semibold">{item.papel_docente}</span>
                  </div>
                  <div className="field-box col-span-2 md:col-span-1">
                    <span className="text-[9px] text-slate-500 block">Fomento</span>
                    <span className={`font-semibold ${item.financiamento_mencionado ? "text-emerald-400" : "text-slate-400"}`}>
                      {item.agencia_fomento || (item.financiamento_mencionado ? "Sim (Verificar)" : "Nenhum")}
                    </span>
                  </div>
                </div>

                {/* Collapsible Original Fragment */}
                <OriginalFragment text={item.trecho_original} />

                {/* Human-in-the-loop actions */}
                <ActionPanel 
                  status={item.status_validacao} 
                  onConfirm={() => d.handleConfirm("projetos", item.id)}
                  onEdit={() => d.handleOpenEdit("projetos", item)}
                  onDiscard={() => d.handleDiscard("projetos", item.id)}
                />
              </div>
            ))}

            {/* EVENTS VIEW */}
            {d.activeTab === "eventos" && d.eventos.map((item) => (
              <div 
                key={item.id} 
                className={`glow-card rounded-xl p-5 border transition-all duration-300 relative overflow-hidden ${
                  item.status_validacao === "confirmado" ? "border-emerald-300 bg-emerald-50" :
                  item.status_validacao === "editado" ? "border-indigo-300 bg-indigo-50" :
                  item.status_validacao === "descartado" ? "border-rose-200 bg-rose-50 opacity-60" : "border-slate-200"
                }`}
              >
                <div className="absolute top-0 left-0 right-0 h-1 flex">
                  <div className={`w-full ${
                    item.status_validacao === "confirmado" ? "bg-emerald-500" :
                    item.status_validacao === "editado" ? "bg-indigo-500" :
                    item.status_validacao === "descartado" ? "bg-rose-500" : "bg-slate-700"
                  }`}></div>
                </div>

                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <span className="text-[10px] px-2 py-0.5 bg-slate-100 border border-slate-300 text-slate-700 rounded font-bold uppercase tracking-wider">
                      {item.eh_organizacao ? "organização" : item.tipo_participacao}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 mt-1">{item.nome_evento}</h3>
                  </div>

                  <ConfidenceBadge level={item.confianca_ia} />
                </div>

                <div className="text-xs text-slate-400 mt-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                  <span className="text-[9px] text-slate-500 block mb-0.5">Trabalho Apresentado</span>
                  <span className="font-semibold text-slate-800">"{item.titulo_trabalho}"</span>
                </div>

                <div className="grid grid-cols-3 gap-3 mt-4 text-[11px] text-slate-300">
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Ano</span>
                    <span className="font-semibold">{item.ano}</span>
                  </div>
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Localidade</span>
                    <span className="font-semibold">{item.cidade}, {item.pais}</span>
                  </div>
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Auxílio Mobilidade</span>
                    <span className={`font-semibold ${item.financiamento_mencionado ? "text-emerald-400" : "text-slate-500"}`}>
                      {item.fonte_financiamento || "Não consta"}
                    </span>
                  </div>
                </div>

                <OriginalFragment text={item.trecho_original} />

                <ActionPanel 
                  status={item.status_validacao} 
                  onConfirm={() => d.handleConfirm("eventos", item.id)}
                  onEdit={() => d.handleOpenEdit("eventos", item)}
                  onDiscard={() => d.handleDiscard("eventos", item.id)}
                />
              </div>
            ))}

            {/* PRODUÇÕES — agrupadas por tipo */}
            {d.activeTab === "producoes" && d.producoesPorTipo.map((group) => (
              <section key={group.tipo} className="space-y-4">
                <div className="flex items-center gap-2 sticky top-24 z-10 py-2 section-sticky">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                    {group.label}
                  </h3>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-400 font-semibold">
                    {group.items.length}
                  </span>
                </div>
                {group.items.map((item) => (
                  <div
                    key={item.id}
                    className={`glow-card rounded-xl p-5 border transition-all duration-300 relative overflow-hidden ${
                      item.status_validacao === "confirmado" ? "border-emerald-300 bg-emerald-50" :
                      item.status_validacao === "editado" ? "border-indigo-300 bg-indigo-50" :
                      item.status_validacao === "descartado" ? "border-rose-200 bg-rose-50 opacity-60" : "border-slate-200"
                    }`}
                  >
                    <div className="absolute top-0 left-0 right-0 h-1 flex">
                      <div className={`w-full ${
                        item.status_validacao === "confirmado" ? "bg-emerald-500" :
                        item.status_validacao === "editado" ? "bg-indigo-500" :
                        item.status_validacao === "descartado" ? "bg-rose-500" : "bg-slate-700"
                      }`}></div>
                    </div>

                    <div className="flex justify-between items-start gap-4">
                      <div className="space-y-1">
                        <span className="text-[10px] px-2 py-0.5 bg-slate-100 border border-slate-300 text-slate-700 rounded font-bold uppercase tracking-wider">
                          {item.tipo}
                        </span>
                        <h3 className="text-sm font-bold text-slate-900 mt-1">{item.titulo}</h3>
                        <ProducaoIndicadores
                          qualis={item.qualis}
                          journal_h_index={item.journal_h_index}
                          scholar_citations={item.scholar_citations}
                          scholar_h5_index={item.scholar_h5_index}
                          scholar_metrics_year={item.scholar_metrics_year}
                        />
                      </div>

                      <ConfidenceBadge level={item.confianca_ia} />
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-[11px] text-slate-300">
                      <div className="field-box">
                        <span className="text-[9px] text-slate-500 block">Ano</span>
                        <span className="font-semibold">{item.ano}</span>
                      </div>
                      <div className="field-box col-span-2 md:col-span-1">
                        <span className="text-[9px] text-slate-500 block">Veículo / Editora</span>
                        <span className="font-semibold truncate block">{item.veiculo}</span>
                      </div>
                      <div className="field-box">
                        <span className="text-[9px] text-slate-500 block">DOI</span>
                        <span className="font-semibold font-mono text-[10px] truncate block text-indigo-400">{item.doi || "N/D"}</span>
                      </div>
                      <div className="field-box">
                        <span className="text-[9px] text-slate-500 block">ISSN / ISBN</span>
                        <span className="font-semibold font-mono text-[10px] truncate block">{item.issn || "N/D"}</span>
                      </div>
                      {item.qualis && (
                        <div className="bg-indigo-50 p-2 rounded-lg border border-indigo-200">
                          <span className="text-[9px] text-indigo-400 block font-bold">Qualis</span>
                          <span className="font-bold text-indigo-300">{item.qualis}</span>
                        </div>
                      )}
                      {item.scholar_citations != null && (
                        <div className="bg-amber-50 p-2 rounded-lg border border-amber-200">
                          <span className="text-[9px] text-amber-700 block font-bold">
                            Citações (Scholar)
                          </span>
                          <span className="font-bold text-amber-900">
                            {item.scholar_citations}
                          </span>
                        </div>
                      )}
                      {item.scholar_h5_index != null && (
                        <div className="bg-emerald-50 p-2 rounded-lg border border-emerald-200">
                          <span className="text-[9px] text-emerald-600 block font-bold">
                            Scholar h5
                          </span>
                          <span className="font-bold text-emerald-800">
                            {item.scholar_h5_index}
                            {item.scholar_h5_median != null ? ` (mediana ${item.scholar_h5_median})` : ""}
                            {item.scholar_metrics_year != null
                              ? ` · ${item.scholar_metrics_year}`
                              : ""}
                          </span>
                        </div>
                      )}
                      {item.journal_h_index != null && (
                        <div className="bg-sky-50 p-2 rounded-lg border border-sky-200">
                          <span className="text-[9px] text-sky-600 block font-bold">
                            H-index revista
                          </span>
                          <span className="font-bold text-sky-800">{item.journal_h_index}</span>
                        </div>
                      )}
                    </div>

                    <OriginalFragment text={item.trecho_original} />

                    <ActionPanel
                      status={item.status_validacao}
                      onConfirm={() => d.handleConfirm("producoes", item.id)}
                      onEdit={() => d.handleOpenEdit("producoes", item)}
                      onDiscard={() => d.handleDiscard("producoes", item.id)}
                    />
                  </div>
                ))}
              </section>
            ))}

            {/* ORIENTAÇÕES — agrupadas por tipo */}
            {d.activeTab === "orientacoes" && d.orientacoesPorTipo.map((group) => (
              <section key={group.tipo} className="space-y-4">
                <div className="flex items-center gap-2 sticky top-24 z-10 py-2 section-sticky">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                    {group.label}
                  </h3>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-400 font-semibold">
                    {group.items.length}
                  </span>
                </div>
                {group.items.map((item) => (
                  <div
                    key={item.id}
                    className={`glow-card rounded-xl p-5 border transition-all duration-300 ${
                      item.status_validacao === "confirmado" ? "border-emerald-300 bg-emerald-50" :
                      item.status_validacao === "editado" ? "border-indigo-300 bg-indigo-50" :
                      item.status_validacao === "descartado" ? "border-rose-200 bg-rose-50 opacity-60" : "border-slate-200"
                    }`}
                  >
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <span className="text-[10px] px-2 py-0.5 bg-slate-100 border border-slate-300 rounded font-bold uppercase">
                          {item.status}
                        </span>
                        <h3 className="text-sm font-bold text-slate-900 mt-2">
                          {item.nome_orientando || "Orientando não identificado"}
                        </h3>
                        {item.titulo_trabalho && (
                          <p className="text-[11px] text-slate-400 mt-1">{item.titulo_trabalho}</p>
                        )}
                      </div>
                      <ConfidenceBadge level={item.confianca_ia} />
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-3 text-[11px] text-slate-300">
                      <div className="field-box">
                        <span className="text-[9px] text-slate-500 block">Início</span>
                        {item.ano_inicio ?? "—"}
                      </div>
                      <div className="field-box">
                        <span className="text-[9px] text-slate-500 block">Conclusão</span>
                        {item.ano_conclusao ?? "—"}
                      </div>
                      <div className="field-box">
                        <span className="text-[9px] text-slate-500 block">Papel</span>
                        {item.papel}
                      </div>
                    </div>
                    <OriginalFragment text={item.trecho_original} />
                    <ActionPanel
                      status={item.status_validacao}
                      onConfirm={() => d.handleConfirm("orientacoes", item.id)}
                      onEdit={() => d.handleOpenEdit("orientacoes", item)}
                      onDiscard={() => d.handleDiscard("orientacoes", item.id)}
                    />
                  </div>
                ))}
              </section>
            ))}

            {/* FORMAÇÃO */}
            {d.activeTab === "formacoes_academicas" && d.formacoes.map((item) => (
              <div
                key={item.id}
                className={`glow-card rounded-xl p-5 border transition-all duration-300 ${
                  item.status_validacao === "confirmado" ? "border-emerald-300 bg-emerald-50" :
                  item.status_validacao === "editado" ? "border-indigo-300 bg-indigo-50" :
                  item.status_validacao === "descartado" ? "border-rose-200 bg-rose-50 opacity-60" : "border-slate-200"
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-[10px] px-2 py-0.5 bg-slate-100 border border-slate-300 rounded font-bold uppercase">
                      {item.nivel}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 mt-2">{item.curso || "Curso não informado"}</h3>
                    <p className="text-[11px] text-slate-400">{item.instituicao}</p>
                  </div>
                  <ConfidenceBadge level={item.confianca_ia} />
                </div>
                <div className="grid grid-cols-2 gap-2 mt-3 text-[11px] text-slate-300">
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Período</span>
                    {item.ano_inicio ?? "?"} — {item.ano_fim ?? "?"}
                  </div>
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Área</span>
                    {item.area_conhecimento || "—"}
                  </div>
                </div>
                <OriginalFragment text={item.trecho_original} />
                <ActionPanel
                  status={item.status_validacao}
                  onConfirm={() => d.handleConfirm("formacoes_academicas", item.id)}
                  onEdit={() => d.handleOpenEdit("formacoes_academicas", item)}
                  onDiscard={() => d.handleDiscard("formacoes_academicas", item.id)}
                />
              </div>
            ))}

            {/* PRODUÇÃO TÉCNICA */}
            {d.activeTab === "producoes_tecnicas" && d.producoesTecnicas.map((item) => (
              <div
                key={item.id}
                className={`glow-card rounded-xl p-5 border transition-all duration-300 ${
                  item.status_validacao === "confirmado" ? "border-emerald-300 bg-emerald-50" :
                  item.status_validacao === "editado" ? "border-indigo-300 bg-indigo-50" :
                  item.status_validacao === "descartado" ? "border-rose-200 bg-rose-50 opacity-60" : "border-slate-200"
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-[10px] px-2 py-0.5 bg-slate-100 border border-slate-300 rounded font-bold uppercase">
                      {item.tipo}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 mt-2">{item.titulo}</h3>
                    {item.instituicao && <p className="text-[11px] text-slate-400 mt-1">{item.instituicao}</p>}
                  </div>
                  <ConfidenceBadge level={item.confianca_ia} />
                </div>
                {item.descricao && (
                  <p className="text-xs text-slate-400 mt-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200">{item.descricao}</p>
                )}
                <div className="grid grid-cols-2 gap-2 mt-3 text-[11px] text-slate-300">
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Ano</span>
                    {item.ano ?? "—"}
                  </div>
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">URL</span>
                    <span className="truncate block text-indigo-400">{item.url || "—"}</span>
                  </div>
                </div>
                <OriginalFragment text={item.trecho_original} />
                <ActionPanel
                  status={item.status_validacao}
                  onConfirm={() => d.handleConfirm("producoes_tecnicas", item.id)}
                  onEdit={() => d.handleOpenEdit("producoes_tecnicas", item)}
                  onDiscard={() => d.handleDiscard("producoes_tecnicas", item.id)}
                />
              </div>
            ))}

            {/* PRÊMIOS */}
            {d.activeTab === "premios" && d.premios.map((item) => (
              <div
                key={item.id}
                className={`glow-card rounded-xl p-5 border transition-all duration-300 ${
                  item.status_validacao === "confirmado" ? "border-emerald-300 bg-emerald-50" :
                  item.status_validacao === "editado" ? "border-indigo-300 bg-indigo-50" :
                  item.status_validacao === "descartado" ? "border-rose-200 bg-rose-50 opacity-60" : "border-slate-200"
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-[10px] px-2 py-0.5 bg-slate-100 border border-slate-300 rounded font-bold uppercase">
                      {item.tipo}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 mt-2">{item.nome}</h3>
                    {item.instituicao_concedente && (
                      <p className="text-[11px] text-slate-400 mt-1">{item.instituicao_concedente}</p>
                    )}
                  </div>
                  <ConfidenceBadge level={item.confianca_ia} />
                </div>
                {item.descricao && (
                  <p className="text-xs text-slate-400 mt-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200">{item.descricao}</p>
                )}
                <div className="grid grid-cols-2 gap-2 mt-3 text-[11px] text-slate-300">
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Ano</span>
                    {item.ano ?? "—"}
                  </div>
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Concedente</span>
                    {item.instituicao_concedente || "—"}
                  </div>
                </div>
                <OriginalFragment text={item.trecho_original} />
                <ActionPanel
                  status={item.status_validacao}
                  onConfirm={() => d.handleConfirm("premios", item.id)}
                  onEdit={() => d.handleOpenEdit("premios", item)}
                  onDiscard={() => d.handleDiscard("premios", item.id)}
                />
              </div>
            ))}

            {/* GRUPOS DE PESQUISA */}
            {d.activeTab === "grupos_pesquisa" && d.gruposPesquisa.map((item) => (
              <div
                key={item.id}
                className={`glow-card rounded-xl p-5 border transition-all duration-300 ${
                  item.status_validacao === "confirmado" ? "border-emerald-300 bg-emerald-50" :
                  item.status_validacao === "editado" ? "border-indigo-300 bg-indigo-50" :
                  item.status_validacao === "descartado" ? "border-rose-200 bg-rose-50 opacity-60" : "border-slate-200"
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-[10px] px-2 py-0.5 bg-slate-100 border border-slate-300 rounded font-bold uppercase">
                      {item.papel}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 mt-2">{item.nome_grupo}</h3>
                    {item.linha_tematica && (
                      <p className="text-[11px] text-slate-400 mt-1">{item.linha_tematica}</p>
                    )}
                  </div>
                  <ConfidenceBadge level={item.confianca_ia} />
                </div>
                <div className="grid grid-cols-3 gap-2 mt-3 text-[11px] text-slate-300">
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Código DGP</span>
                    {item.codigo_dgp || "—"}
                  </div>
                  <div className="field-box col-span-2">
                    <span className="text-[9px] text-slate-500 block">Instituição</span>
                    {item.instituicao || "—"}
                  </div>
                </div>
                <OriginalFragment text={item.trecho_original} />
                <ActionPanel
                  status={item.status_validacao}
                  onConfirm={() => d.handleConfirm("grupos_pesquisa", item.id)}
                  onEdit={() => d.handleOpenEdit("grupos_pesquisa", item)}
                  onDiscard={() => d.handleDiscard("grupos_pesquisa", item.id)}
                />
              </div>
            ))}

            {/* FUNDING VIEW */}
            {d.activeTab === "financiamentos" && d.financiamentos.map((item) => (
              <div 
                key={item.id} 
                className={`glow-card rounded-xl p-5 border transition-all duration-300 relative overflow-hidden ${
                  item.status_validacao === "confirmado" ? "border-emerald-300 bg-emerald-50" :
                  item.status_validacao === "editado" ? "border-indigo-300 bg-indigo-50" :
                  item.status_validacao === "descartado" ? "border-rose-200 bg-rose-50 opacity-60" : "border-slate-200"
                }`}
              >
                <div className="absolute top-0 left-0 right-0 h-1 flex">
                  <div className={`w-full ${
                    item.status_validacao === "confirmado" ? "bg-emerald-500" :
                    item.status_validacao === "editado" ? "bg-indigo-500" :
                    item.status_validacao === "descartado" ? "bg-rose-500" : "bg-slate-700"
                  }`}></div>
                </div>

                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <span className="text-[10px] px-2 py-0.5 bg-slate-100 border border-slate-300 text-slate-700 rounded font-bold uppercase tracking-wider">
                      {item.tipo}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 mt-1">{item.fonte}</h3>
                  </div>

                  <ConfidenceBadge level={item.confianca} />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-[11px] text-slate-300">
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Agência</span>
                    <span className="font-semibold block truncate">{item.agencia}</span>
                  </div>
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Edital</span>
                    <span className="font-semibold block truncate">{item.edital || "Não identificado"}</span>
                  </div>
                  <div className="field-box">
                    <span className="text-[9px] text-slate-500 block">Processo</span>
                    <span className="font-semibold block font-mono text-[10px]">{item.numero_processo || "Não consta"}</span>
                  </div>
                  <div className="bg-slate-50 p-2 rounded border border-emerald-950">
                    <span className="text-[9px] text-emerald-500 block font-bold">Valor Captado</span>
                    <span className="font-bold text-emerald-400 text-xs">{item.valor}</span>
                  </div>
                </div>

                <OriginalFragment text={item.trecho_original} />

                <ActionPanel 
                  status={item.status_validacao} 
                  onConfirm={() => d.handleConfirm("financiamentos", item.id)}
                  onEdit={() => d.handleOpenEdit("financiamentos", item)}
                  onDiscard={() => d.handleDiscard("financiamentos", item.id)}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Right Side: Gaps & Realtime Audit Logs (3 Cols) */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* AI Gap Detection Card */}
          <div className="glow-card rounded-xl p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-sm font-semibold tracking-wider text-slate-600 uppercase flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                Lacunas de Informação
              </h2>
              <span className="text-xs px-2 py-0.5 bg-amber-950 text-amber-400 border border-amber-900 rounded font-semibold">
                {d.lacunas.filter(l => !l.resolvido).length}
              </span>
            </div>

            <div className="space-y-3.5">
              {d.lacunas.length === 0 ? (
                <div className="text-center py-6 text-slate-500 text-xs">
                  <CheckCircle className="w-8 h-8 text-emerald-600/80 mx-auto mb-2" />
                  Nenhuma lacuna detectada para este docente!
                </div>
              ) : (
                d.lacunas.map((gap) => (
                  <div 
                    key={gap.id}
                    className={`p-3 rounded-lg border transition-all duration-300 ${
                      gap.resolvido 
                        ? "bg-slate-50/40 border-slate-200/60 opacity-30" 
                        : "bg-slate-50 border-slate-200 hover:border-slate-800"
                    }`}
                  >
                    <div className="flex justify-between items-center w-full">
                      <span className="font-bold text-[10px] text-slate-400 uppercase tracking-wider">{gap.tipo_lacuna}</span>
                      {!gap.resolvido && (
                        <span className={`text-[9px] px-1.5 py-0.2 rounded font-bold uppercase tracking-wider ${
                          gap.gravidade === "alta" ? "bg-rose-950 text-rose-400 border border-rose-900" :
                          gap.gravidade === "media" ? "bg-amber-950 text-amber-400 border border-amber-900" :
                          "bg-blue-950 text-blue-400 border border-blue-900"
                        }`}>
                          {gap.gravidade}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-300 mt-2 leading-relaxed">{gap.descricao}</p>
                    
                    {!gap.resolvido && (
                      <div className="mt-2.5 pt-2 border-t border-slate-200 flex justify-between items-center">
                        <span className="text-[9px] text-slate-500 max-w-[70%] leading-snug">{gap.acao_recomendada}</span>
                        <button 
                          onClick={() => d.handleResolveGap(gap.id)}
                          className="py-1 px-2 bg-indigo-950/60 hover:bg-indigo-900/60 border border-indigo-800 text-[10px] text-indigo-400 font-semibold rounded transition-colors"
                        >
                          Resolver
                        </button>
                      </div>
                    )}

                    {gap.resolvido && (
                      <div className="mt-2.5 pt-2 border-t border-slate-200 flex items-center gap-1.5 text-[10px] text-emerald-500 font-bold">
                        <Check className="w-3.5 h-3.5" />
                        Resolvido
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Audit Log Card */}
          <div className="glow-card rounded-xl p-5">
            <h2 className="text-sm font-semibold tracking-wider text-slate-600 uppercase mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-400" />
              Logs de Validação
            </h2>

            <div className="space-y-3 max-h-[220px] overflow-y-auto pr-1">
              {d.auditLogs.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
                  Aguardando interações humanas...
                </div>
              ) : (
                d.auditLogs.map((log) => (
                  <div key={log.id} className="text-[10px] bg-slate-50 p-2.5 border border-slate-200 rounded-lg flex flex-col gap-1">
                    <div className="flex justify-between items-center text-slate-500">
                      <span className={`font-bold uppercase tracking-wider px-1 py-0.2 rounded text-[8px] ${
                        log.acao === "confirmar" ? "bg-emerald-950/80 text-emerald-400 border border-emerald-900/80" :
                        log.acao === "editar" ? "bg-indigo-950/80 text-indigo-400 border border-indigo-900/80" :
                        log.acao === "descartar" ? "bg-rose-950/80 text-rose-400 border border-rose-900/80" :
                        "bg-slate-900 text-slate-400 border border-slate-800"
                      }`}>
                        {log.acao}
                      </span>
                      <span>{log.timestamp}</span>
                    </div>
                    <span className="text-slate-300 leading-normal">{log.mensagem}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
  );
}
