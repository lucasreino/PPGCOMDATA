"use client";

import { useState } from "react";
import { Upload, Plus } from "lucide-react";
import { apiFetch } from "@/lib/api";

type CatalogKind = "eventos-institucionais" | "egressos" | "processos-seletivos";

const LABELS: Record<CatalogKind, string> = {
  "eventos-institucionais": "Eventos institucionais (SIMCOM, COMPÓS…)",
  egressos: "Egressos",
  "processos-seletivos": "Processos seletivos",
};

interface Props {
  kind: CatalogKind;
  onImported: () => void;
}

export function CatalogPanel({ kind, onImported }: Props) {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [eventoForm, setEventoForm] = useState({
    nome: "",
    edicao: "",
    ano: "",
    numero_inscritos: "",
    agencias_financiadoras: "",
  });

  const uploadCsv = async (file: File) => {
    setLoading(true);
    setMsg(null);
    const fd = new FormData();
    fd.append("file", file);
    const token = typeof window !== "undefined" ? localStorage.getItem("ppgcomdata_token") : null;
    const base = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
    const res = await fetch(`${base}/dossie-apcn/catalog/${kind}/import-csv`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
    });
    setLoading(false);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      setMsg(err.detail || "Falha na importação.");
      return;
    }
    const data = await res.json();
    setMsg(`${data.importados} registro(s) importado(s).`);
    onImported();
  };

  const createEvento = async () => {
    if (!eventoForm.nome.trim()) return;
    setLoading(true);
    const res = await apiFetch(`/dossie-apcn/catalog/eventos-institucionais`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nome: eventoForm.nome,
        edicao: eventoForm.edicao || null,
        ano: eventoForm.ano ? parseInt(eventoForm.ano, 10) : null,
        numero_inscritos: eventoForm.numero_inscritos
          ? parseInt(eventoForm.numero_inscritos, 10)
          : null,
        agencias_financiadoras: eventoForm.agencias_financiadoras || null,
      }),
    });
    setLoading(false);
    if (res.ok) {
      setEventoForm({ nome: "", edicao: "", ano: "", numero_inscritos: "", agencias_financiadoras: "" });
      setMsg("Evento cadastrado.");
      onImported();
    } else {
      setMsg("Erro ao cadastrar evento.");
    }
  };

  return (
    <div className="glow-card rounded-xl p-4 space-y-4 border border-slate-800">
      <h4 className="text-xs font-bold uppercase text-slate-400 tracking-wider">
        Cadastro — {LABELS[kind]}
      </h4>
      <label className="flex items-center gap-2 px-4 py-2.5 bg-slate-950 border border-slate-700 rounded-lg cursor-pointer hover:border-indigo-600 text-xs text-slate-300 w-fit">
        <Upload className="w-4 h-4" />
        Importar CSV
        <input
          type="file"
          accept=".csv"
          className="hidden"
          disabled={loading}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) uploadCsv(f);
          }}
        />
      </label>
      {kind === "eventos-institucionais" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          <input
            placeholder="Nome (ex: SIMCOM)"
            value={eventoForm.nome}
            onChange={(e) => setEventoForm({ ...eventoForm, nome: e.target.value })}
            className="bg-slate-950 border border-slate-800 rounded p-2 text-xs"
          />
          <input
            placeholder="Edição"
            value={eventoForm.edicao}
            onChange={(e) => setEventoForm({ ...eventoForm, edicao: e.target.value })}
            className="bg-slate-950 border border-slate-800 rounded p-2 text-xs"
          />
          <input
            placeholder="Ano"
            value={eventoForm.ano}
            onChange={(e) => setEventoForm({ ...eventoForm, ano: e.target.value })}
            className="bg-slate-950 border border-slate-800 rounded p-2 text-xs"
          />
          <input
            placeholder="Inscritos"
            value={eventoForm.numero_inscritos}
            onChange={(e) => setEventoForm({ ...eventoForm, numero_inscritos: e.target.value })}
            className="bg-slate-950 border border-slate-800 rounded p-2 text-xs"
          />
          <input
            placeholder="Agências financiadoras"
            value={eventoForm.agencias_financiadoras}
            onChange={(e) => setEventoForm({ ...eventoForm, agencias_financiadoras: e.target.value })}
            className="bg-slate-950 border border-slate-800 rounded p-2 text-xs md:col-span-2"
          />
          <button
            type="button"
            onClick={createEvento}
            disabled={loading}
            className="flex items-center justify-center gap-1 py-2 bg-indigo-600 rounded text-xs font-bold text-white"
          >
            <Plus className="w-3 h-3" /> Adicionar
          </button>
        </div>
      )}
      {msg && <p className="text-xs text-slate-400">{msg}</p>}
      <p className="text-[10px] text-slate-500">
        CSV com cabeçalho na primeira linha. Colunas devem corresponder aos campos do cadastro.
      </p>
    </div>
  );
}

export function ExportButtons({ query }: { query: string }) {
  const base = typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL || `http://${window.location.hostname}:8000/api/v1`).replace(/\/$/, "")
    : "";
  const token = typeof window !== "undefined" ? localStorage.getItem("ppgcomdata_token") : null;

  const download = async (path: string, filename: string) => {
    const res = await fetch(`${base}${path}${query}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const items = [
    ["producao.csv", "producao_docente.csv"],
    ["financiamento.csv", "financiamento.csv"],
    ["projetos.csv", "projetos.csv"],
    ["eventos.csv", "eventos.csv"],
    ["lacunas.csv", "lacunas.csv"],
    ["egressos.csv", "egressos.csv"],
    ["resumo.md", "resumo_ppgcom.md"],
  ] as const;

  return (
    <div className="flex flex-wrap gap-2">
      {items.map(([path, file]) => (
        <button
          key={path}
          type="button"
          onClick={() => download(`/dossie-apcn/export/${path}`, file)}
          className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs hover:border-indigo-600"
        >
          {file}
        </button>
      ))}
    </div>
  );
}
