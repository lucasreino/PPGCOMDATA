"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { ProfessorCatalog, ProfessorResumo } from "@/lib/types";
import {
  mapProfessorDados,
  resumoFromApi,
  type ProfessorDadosPayload,
} from "@/lib/map-professor-dados";
import { ProfessorProfileView } from "@/components/docentes/ProfessorProfileView";

export default function DocenteProfilePage() {
  const params = useParams();
  const id = typeof params.id === "string" ? params.id : "";
  const [prof, setProf] = useState<ProfessorCatalog | null>(null);
  const [dados, setDados] = useState<ProfessorDadosPayload | null>(null);
  const [resumo, setResumo] = useState<ProfessorResumo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError("");

    (async () => {
      try {
        const [catalogRes, dadosRes, resumoRes] = await Promise.all([
          apiFetch(`/professores/${id}/catalog`),
          apiFetch(`/professores/${id}/dados`),
          apiFetch(`/professores/${id}/resumo-academico`),
        ]);
        if (!catalogRes.ok) {
          throw new Error("Professor não encontrado.");
        }
        const found: ProfessorCatalog = await catalogRes.json();

        if (!dadosRes.ok) {
          const errBody = await dadosRes.json().catch(() => ({}));
          const detail =
            typeof errBody.detail === "string"
              ? errBody.detail
              : `Erro ${dadosRes.status} ao carregar dados do docente.`;
          throw new Error(detail);
        }

        const rawDados = await dadosRes.json();
        setProf(found);
        setDados(mapProfessorDados(rawDados));
        if (resumoRes.ok) {
          setResumo(resumoFromApi(await resumoRes.json()));
        } else {
          setResumo(null);
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Erro ao carregar perfil.";
        if (msg === "Failed to fetch") {
          setError(
            "Falha de conexão com a API. Verifique se o servidor está online e se a URL da API está correta."
          );
        } else {
          setError(msg);
        }
        setProf(null);
        setDados(null);
        setResumo(null);
      }
    })()
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div>
      <Link
        href="/docentes"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-indigo-300 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Voltar ao corpo docente
      </Link>

      {loading && (
        <p className="text-sm text-slate-500 text-center py-20">Carregando perfil...</p>
      )}
      {error && (
        <p className="text-sm text-rose-400 text-center py-20">{error}</p>
      )}
      {!loading && !error && prof && dados && (
        <ProfessorProfileView prof={prof} dados={dados} resumo={resumo} />
      )}
    </div>
  );
}
