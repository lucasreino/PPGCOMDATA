"use client";

import { RefreshCw } from "lucide-react";

export interface FilterState {
  professorId: string;
  linhaId: string;
  anoInicio: string;
  anoFim: string;
  apenasValidados: boolean;
}

interface Props {
  filters: FilterState;
  onChange: (f: FilterState) => void;
  onRefresh: () => void;
  loading?: boolean;
  professores: { id: string; nome_completo: string }[];
  linhas: { id: string; nome: string }[];
}

export function DossieFiltersBar({
  filters,
  onChange,
  onRefresh,
  loading,
  professores,
  linhas,
}: Props) {
  const set = (patch: Partial<FilterState>) => onChange({ ...filters, ...patch });

  return (
    <div className="glow-card rounded-xl p-5 flex flex-wrap gap-4 items-end">
      <div className="flex-1 min-w-[180px] space-y-1.5">
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Docente</label>
        <select
          value={filters.professorId}
          onChange={(e) => set({ professorId: e.target.value })}
          className="w-full input-field p-2.5 rounded text-xs text-slate-200"
        >
          <option value="">Todos</option>
          {professores.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nome_completo}
            </option>
          ))}
        </select>
      </div>
      <div className="flex-1 min-w-[180px] space-y-1.5">
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Linha</label>
        <select
          value={filters.linhaId}
          onChange={(e) => set({ linhaId: e.target.value })}
          className="w-full input-field p-2.5 rounded text-xs text-slate-200"
        >
          <option value="">Todas</option>
          {linhas.map((l) => (
            <option key={l.id} value={l.id}>
              {l.nome}
            </option>
          ))}
        </select>
      </div>
      <div className="w-[100px] space-y-1.5">
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano início</label>
        <input
          type="number"
          value={filters.anoInicio}
          onChange={(e) => set({ anoInicio: e.target.value })}
          className="w-full input-field p-2.5 rounded text-xs text-slate-200"
          placeholder="2015"
        />
      </div>
      <div className="w-[100px] space-y-1.5">
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ano fim</label>
        <input
          type="number"
          value={filters.anoFim}
          onChange={(e) => set({ anoFim: e.target.value })}
          className="w-full input-field p-2.5 rounded text-xs text-slate-200"
          placeholder="2026"
        />
      </div>
      <label className="flex items-center gap-2 text-xs text-slate-300 pb-2 cursor-pointer">
        <input
          type="checkbox"
          checked={filters.apenasValidados}
          onChange={(e) => set({ apenasValidados: e.target.checked })}
          className="rounded border-slate-600"
        />
        Só validados
      </label>
      <button
        type="button"
        onClick={onRefresh}
        className="py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-bold text-xs flex items-center gap-2"
      >
        <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        Atualizar
      </button>
    </div>
  );
}

export function buildDossieQuery(f: FilterState): string {
  const q = new URLSearchParams();
  if (f.professorId) q.set("professor_id", f.professorId);
  if (f.linhaId) q.set("linha_pesquisa_id", f.linhaId);
  if (f.anoInicio) q.set("ano_inicio", f.anoInicio);
  if (f.anoFim) q.set("ano_fim", f.anoFim);
  if (f.apenasValidados) q.set("apenas_validados", "true");
  const s = q.toString();
  return s ? `?${s}` : "";
}
