"use client";

import React from "react";
import { Check, Edit2 } from "lucide-react";
import type { EntityTab } from "@/lib/types";
import { useDashboard } from "./DashboardProvider";

export function ValidationEditModal() {
  const d = useDashboard();
  return (
    <>
      {d.editingItem && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl shadow-2xl max-w-lg w-full overflow-hidden glow-card">
            <div className="border-b border-slate-200 p-4 flex justify-between items-center">
              <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <Edit2 className="w-4.5 h-4.5 text-indigo-400" />
                Editar e Corrigir {({
                  projetos: "Projeto",
                  eventos: "Evento",
                  producoes: "Produção",
                  financiamentos: "Financiamento",
                  orientacoes: "Orientação",
                  formacoes_academicas: "Formação",
                  producoes_tecnicas: "Produção Técnica",
                  premios: "Prêmio",
                  grupos_pesquisa: "Grupo de Pesquisa",
                } as Record<EntityTab, string>)[d.editingItem.type as EntityTab] || "Registro"}
              </h3>
              <button 
                onClick={() => d.setEditingItem(null)}
                className="text-slate-400 hover:text-slate-200 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="p-5 space-y-4 max-h-[60vh] overflow-y-auto">
              
              {/* If Project */}
              {d.editingItem.type === "projetos" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Título do Projeto</label>
                    <input 
                      type="text" 
                      value={d.editingItem.item.titulo} 
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, titulo: e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 hover:border-slate-300 focus:border-indigo-600 outline-none p-2.5 rounded text-xs text-slate-200"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Início</label>
                      <input 
                        type="number" 
                        value={d.editingItem.item.ano_inicio} 
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, ano_inicio: parseInt(e.target.value) } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano Fim</label>
                      <input 
                        type="number" 
                        value={d.editingItem.item.ano_fim || ""} 
                        placeholder="Atual"
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, ano_fim: e.target.value ? parseInt(e.target.value) : null } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Descrição</label>
                    <textarea 
                      rows={3}
                      value={d.editingItem.item.descricao} 
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, descricao: e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 hover:border-slate-300 focus:border-indigo-600 outline-none p-2.5 rounded text-xs text-slate-200"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Agência de Fomento</label>
                    <input 
                      type="text" 
                      value={d.editingItem.item.agencia_fomento || ""} 
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, agencia_fomento: e.target.value, financiamento_mencionado: !!e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                </>
              )}

              {/* If Event */}
              {d.editingItem.type === "eventos" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Nome do Evento</label>
                    <input 
                      type="text" 
                      value={d.editingItem.item.nome_evento} 
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, nome_evento: e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Trabalho Apresentado</label>
                    <input 
                      type="text" 
                      value={d.editingItem.item.titulo_trabalho} 
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, titulo_trabalho: e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano</label>
                      <input 
                        type="number" 
                        value={d.editingItem.item.ano} 
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, ano: parseInt(e.target.value) } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Cidade</label>
                      <input 
                        type="text" 
                        value={d.editingItem.item.cidade} 
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, cidade: e.target.value } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">País</label>
                      <input 
                        type="text" 
                        value={d.editingItem.item.pais} 
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, pais: e.target.value } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* If Production */}
              {d.editingItem.type === "producoes" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Título</label>
                    <input 
                      type="text" 
                      value={d.editingItem.item.titulo} 
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, titulo: e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Veículo / Revista / Editora</label>
                    <input 
                      type="text" 
                      value={d.editingItem.item.veiculo} 
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, veiculo: e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano</label>
                      <input 
                        type="number" 
                        value={d.editingItem.item.ano} 
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, ano: parseInt(e.target.value) } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1 col-span-2">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">DOI</label>
                      <input 
                        type="text" 
                        value={d.editingItem.item.doi || ""} 
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, doi: e.target.value || null } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none font-mono"
                      />
                    </div>
                  </div>
                </>
              )}

              {d.editingItem.type === "producoes_tecnicas" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Título</label>
                    <input
                      type="text"
                      value={d.editingItem.item.titulo}
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, titulo: e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Tipo</label>
                      <input
                        type="text"
                        value={d.editingItem.item.tipo}
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, tipo: e.target.value } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano</label>
                      <input
                        type="number"
                        value={d.editingItem.item.ano ?? ""}
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, ano: e.target.value ? parseInt(e.target.value) : null } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Instituição</label>
                    <input
                      type="text"
                      value={d.editingItem.item.instituicao || ""}
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, instituicao: e.target.value || null } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Descrição</label>
                    <textarea
                      rows={2}
                      value={d.editingItem.item.descricao || ""}
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, descricao: e.target.value || null } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                </>
              )}

              {d.editingItem.type === "premios" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Nome do prêmio / título</label>
                    <input
                      type="text"
                      value={d.editingItem.item.nome}
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, nome: e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Tipo</label>
                      <input
                        type="text"
                        value={d.editingItem.item.tipo}
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, tipo: e.target.value } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano</label>
                      <input
                        type="number"
                        value={d.editingItem.item.ano ?? ""}
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, ano: e.target.value ? parseInt(e.target.value) : null } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Instituição concedente</label>
                    <input
                      type="text"
                      value={d.editingItem.item.instituicao_concedente || ""}
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, instituicao_concedente: e.target.value || null } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                </>
              )}

              {d.editingItem.type === "grupos_pesquisa" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Nome do grupo</label>
                    <input
                      type="text"
                      value={d.editingItem.item.nome_grupo}
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, nome_grupo: e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Papel</label>
                      <input
                        type="text"
                        value={d.editingItem.item.papel}
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, papel: e.target.value } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Código DGP</label>
                      <input
                        type="text"
                        value={d.editingItem.item.codigo_dgp || ""}
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, codigo_dgp: e.target.value || null } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none font-mono"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Linha temática</label>
                    <input
                      type="text"
                      value={d.editingItem.item.linha_tematica || ""}
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, linha_tematica: e.target.value || null } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Instituição</label>
                    <input
                      type="text"
                      value={d.editingItem.item.instituicao || ""}
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, instituicao: e.target.value || null } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                </>
              )}

              {/* If Funding */}
              {d.editingItem.type === "financiamentos" && (
                <>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Fonte de Recurso</label>
                    <input 
                      type="text" 
                      value={d.editingItem.item.fonte} 
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, fonte: e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Agência de Fomento</label>
                    <input 
                      type="text" 
                      value={d.editingItem.item.agencia} 
                      onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, agencia: e.target.value } })}
                      className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Número Processo / Edital</label>
                      <input 
                        type="text" 
                        value={d.editingItem.item.numero_processo || ""} 
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, numero_processo: e.target.value || null } })}
                        className="w-full bg-slate-50 border border-slate-800 p-2.5 rounded text-xs text-slate-200 outline-none font-mono"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-emerald-500">Valor Captado</label>
                      <input 
                        type="text" 
                        value={d.editingItem.item.valor} 
                        onChange={(e) => d.setEditingItem({ ...d.editingItem, item: { ...d.editingItem.item, valor: e.target.value } })}
                        className="w-full bg-slate-50 border border-emerald-950 p-2.5 rounded text-xs text-slate-200 outline-none font-bold text-emerald-400"
                      />
                    </div>
                  </div>
                </>
              )}

            </div>

            <div className="border-t border-slate-200 p-4 flex justify-end gap-3 bg-slate-50">
              <button 
                onClick={() => d.setEditingItem(null)}
                className="py-1.5 px-3 bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-400 rounded-lg hover:text-slate-200 transition-colors"
              >
                Cancelar
              </button>
              <button 
                onClick={d.handleSaveEdit}
                className="py-1.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white rounded-lg shadow-lg shadow-indigo-600/10 transition-all flex items-center gap-1.5"
              >
                <Check className="w-4 h-4" />
                Salvar & Validar
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
