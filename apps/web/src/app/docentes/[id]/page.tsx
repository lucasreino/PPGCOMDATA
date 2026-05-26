"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { cacheKey, cachedJson, isCacheValid } from "@/lib/api-cache";
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
    const allCached =
      isCacheValid(cacheKey("professor", "catalog", id)) &&
      isCacheValid(cacheKey("professor", "dados", id)) &&
      isCacheValid(cacheKey("professor", "resumo", id));
    if (!allCached) setLoading(true);
    setError("");

    (async () => {
      try {
        const found = await cachedJson(
          cacheKey("professor", "catalog", id),
          async () => {
            const catalogRes = await apiFetch(`/professores/${id}/catalog`);
            if (!catalogRes.ok) throw new Error("Professor não encontrado.");
            return catalogRes.json() as Promise<ProfessorCatalog>;
          }
        );

        const rawDados = await cachedJson(
          cacheKey("professor", "dados", id),
          async () => {
            const dadosRes = await apiFetch(`/professores/${id}/dados`);
            if (!dadosRes.ok) {
              const errBody = await dadosRes.json().catch(() => ({}));
              const detail =
                typeof errBody.detail === "string"
                  ? errBody.detail
                  : `Erro ${dadosRes.status} ao carregar dados do docente.`;
              throw new Error(detail);
            }
            return dadosRes.json();
          }
        );

        const resumoRaw = await cachedJson(
          cacheKey("professor", "resumo", id),
          async () => {
            const resumoRes = await apiFetch(`/professores/${id}/resumo-academico`);
            return resumoRes.ok ? resumoRes.json() : null;
          }
        );

        setProf(found);
        setDados(mapProfessorDados(rawDados));
        setResumo(resumoRaw ? resumoFromApi(resumoRaw) : null);
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
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-indigo-600 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Voltar ao corpo docente
      </Link>

      {loading && (
        <p className="text-sm text-slate-500 text-center py-20">Carregando perfil...</p>
      )}
      {error && (
        <p className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-lg px-4 py-3 text-center max-w-lg mx-auto">
          {error}
        </p>
      )}
      {!loading && !error && prof && dados && (
        <ProfessorProfileView prof={prof} dados={dados} resumo={resumo} />
      )}
    </div>
  );
}
