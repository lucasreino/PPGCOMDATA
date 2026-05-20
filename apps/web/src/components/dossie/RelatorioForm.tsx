"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface Props {
  professores: { id: string; nome_completo: string }[];
  linhas: { id: string; nome: string }[];
  onSaved: () => void;
}

export function RelatorioForm({ professores, linhas, onSaved }: Props) {
  const [open, setOpen] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [form, setForm] = useState({
    professor_id: "",
    titulo: "",
    tipo: "extensao",
    linha_pesquisa_id: "",
    tema_principal: "",
    publico_atendido: "",
    territorio_impactado: "",
    produto_gerado: "",
    impacto_social: "",
    tipo_impacto: "regional",
    possui_financiamento_confirmado: false,
  });

  const save = async () => {
    if (!form.professor_id || !form.titulo.trim()) {
      setMsg("Informe docente e título.");
      return;
    }
    const res = await apiFetch("/relatorios-projeto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...form,
        linha_pesquisa_id: form.linha_pesquisa_id || null,
        possui_financiamento_confirmado: form.possui_financiamento_confirmado,
        houve_financiamento: form.possui_financiamento_confirmado,
      }),
    });
    if (!res.ok) {
      setMsg("Erro ao salvar relatório.");
      return;
    }
    setMsg("Relatório cadastrado.");
    setForm({
      professor_id: "",
      titulo: "",
      tipo: "extensao",
      linha_pesquisa_id: "",
      tema_principal: "",
      publico_atendido: "",
      territorio_impactado: "",
      produto_gerado: "",
      impacto_social: "",
      tipo_impacto: "regional",
      possui_financiamento_confirmado: false,
    });
    onSaved();
  };

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 px-4 py-2 bg-emerald-700 hover:bg-emerald-600 rounded-lg text-xs font-bold text-white"
      >
        <Plus className="w-4 h-4" /> Cadastrar relatório de extensão/impacto
      </button>
    );
  }

  return (
    <div className="glow-card rounded-xl p-4 space-y-3 border border-emerald-900/40">
      <h4 className="text-xs font-bold uppercase text-emerald-400 tracking-wider">
        Novo relatório complementar (impacto social)
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        <select
          value={form.professor_id}
          onChange={(e) => setForm({ ...form, professor_id: e.target.value })}
          className="bg-slate-950 border border-slate-800 rounded p-2 text-xs"
        >
          <option value="">Docente</option>
          {professores.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nome_completo}
            </option>
          ))}
        </select>
        <select
          value={form.linha_pesquisa_id}
          onChange={(e) => setForm({ ...form, linha_pesquisa_id: e.target.value })}
          className="bg-slate-950 border border-slate-800 rounded p-2 text-xs"
        >
          <option value="">Linha (opcional)</option>
          {linhas.map((l) => (
            <option key={l.id} value={l.id}>
              {l.nome}
            </option>
          ))}
        </select>
        <input
          placeholder="Título do projeto/ação"
          value={form.titulo}
          onChange={(e) => setForm({ ...form, titulo: e.target.value })}
          className="bg-slate-950 border border-slate-800 rounded p-2 text-xs md:col-span-2"
        />
        <input
          placeholder="Tema principal"
          value={form.tema_principal}
          onChange={(e) => setForm({ ...form, tema_principal: e.target.value })}
          className="bg-slate-950 border border-slate-800 rounded p-2 text-xs"
        />
        <input
          placeholder="Público atendido"
          value={form.publico_atendido}
          onChange={(e) => setForm({ ...form, publico_atendido: e.target.value })}
          className="bg-slate-950 border border-slate-800 rounded p-2 text-xs"
        />
        <input
          placeholder="Território impactado"
          value={form.territorio_impactado}
          onChange={(e) => setForm({ ...form, territorio_impactado: e.target.value })}
          className="bg-slate-950 border border-slate-800 rounded p-2 text-xs"
        />
        <input
          placeholder="Produto gerado"
          value={form.produto_gerado}
          onChange={(e) => setForm({ ...form, produto_gerado: e.target.value })}
          className="bg-slate-950 border border-slate-800 rounded p-2 text-xs"
        />
        <textarea
          placeholder="Resumo do impacto social"
          value={form.impacto_social}
          onChange={(e) => setForm({ ...form, impacto_social: e.target.value })}
          className="bg-slate-950 border border-slate-800 rounded p-2 text-xs md:col-span-2 min-h-[60px]"
        />
      </div>
      <label className="flex items-center gap-2 text-xs text-slate-300">
        <input
          type="checkbox"
          checked={form.possui_financiamento_confirmado}
          onChange={(e) =>
            setForm({ ...form, possui_financiamento_confirmado: e.target.checked })
          }
        />
        Financiamento confirmado
      </label>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={save}
          className="px-4 py-2 bg-indigo-600 rounded text-xs font-bold text-white"
        >
          Salvar
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="px-4 py-2 border border-slate-700 rounded text-xs text-slate-400"
        >
          Fechar
        </button>
      </div>
      {msg && <p className="text-xs text-slate-400">{msg}</p>}
    </div>
  );
}
