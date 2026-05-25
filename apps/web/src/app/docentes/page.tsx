"use client";

import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { ProfessorCatalog } from "@/lib/types";
import { ProfessorCard } from "@/components/docentes/ProfessorCard";

export default function DocentesPage() {
  const [professors, setProfessors] = useState<ProfessorCatalog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");

  useEffect(() => {
    apiFetch("/professores/catalog")
      .then((res) => {
        if (!res.ok) throw new Error("Não foi possível carregar o corpo docente.");
        return res.json();
      })
      .then((data: ProfessorCatalog[]) => setProfessors(data))
      .catch((e) => setError(e instanceof Error ? e.message : "Erro ao carregar."))
      .finally(() => setLoading(false));
  }, []);

  const filtered = professors.filter((p) => {
    const q = query.trim().toLowerCase();
    if (!q) return true;
    const linha = p.linha_pesquisa?.nome?.toLowerCase() ?? "";
    return (
      p.nome_completo.toLowerCase().includes(q) ||
      linha.includes(q) ||
      (p.tipo_docente || "").toLowerCase().includes(q)
    );
  });

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Corpo Docente</h2>
        <p className="text-sm text-slate-600 mt-1">
          Selecione um professor para ver o dossiê completo de produção acadêmica.
        </p>
      </div>

      <div className="relative mb-8 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="search"
          placeholder="Buscar por nome ou linha..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="input-field pl-10 shadow-sm"
        />
      </div>

      {loading && (
        <p className="text-sm text-slate-600 text-center py-16">Carregando docentes...</p>
      )}
      {error && (
        <p className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-lg px-4 py-3 text-center max-w-md mx-auto">
          {error}
        </p>
      )}
      {!loading && !error && filtered.length === 0 && (
        <p className="text-sm text-slate-500 text-center py-16">
          Nenhum docente encontrado.
        </p>
      )}
      {!loading && !error && filtered.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {filtered.map((p) => (
            <ProfessorCard key={p.id} prof={p} />
          ))}
        </div>
      )}
    </div>
  );
}
