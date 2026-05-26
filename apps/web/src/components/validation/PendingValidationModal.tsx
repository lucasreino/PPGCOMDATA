"use client";

import React, { useEffect, useMemo, useState } from "react";
import { X, RefreshCw, ArrowRight, AlertTriangle } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { cacheKey, cachedJson } from "@/lib/api-cache";
import { sortByNewestFirst } from "@/lib/sort-entities";
import type { EntityTab, Professor } from "@/lib/types";

const ENTITY_KEYS: EntityTab[] = [
  "projetos",
  "eventos",
  "producoes",
  "financiamentos",
  "orientacoes",
  "formacoes_academicas",
  "producoes_tecnicas",
  "premios",
  "grupos_pesquisa",
];

const ENTITY_LABELS: Record<EntityTab, string> = {
  projetos: "Projetos",
  eventos: "Eventos",
  producoes: "Produções",
  financiamentos: "Financiamentos",
  orientacoes: "Orientações",
  formacoes_academicas: "Formação acadêmica",
  producoes_tecnicas: "Produção técnica",
  premios: "Prêmios",
  grupos_pesquisa: "Grupos de pesquisa",
};

type PendingPayload = Record<string, unknown[]>;

function itemTitle(entity: EntityTab, item: Record<string, unknown>): string {
  const pick = (...keys: string[]) => {
    for (const k of keys) {
      const v = item[k];
      if (typeof v === "string" && v.trim()) return v.trim();
    }
    return null;
  };
  switch (entity) {
    case "orientacoes":
      return pick("nome_orientando", "titulo_trabalho", "titulo") ?? "Orientação";
    case "formacoes_academicas":
      return pick("curso", "instituicao", "titulo") ?? "Formação";
    case "financiamentos":
      return pick("titulo_projeto", "agencia", "titulo") ?? "Financiamento";
    case "grupos_pesquisa":
      return pick("nome_grupo", "titulo") ?? "Grupo de pesquisa";
    case "premios":
      return pick("nome_premio", "titulo") ?? "Prêmio";
    case "producoes_tecnicas":
      return pick("titulo", "tipo") ?? "Produção técnica";
    default:
      return pick("titulo", "nome", "descricao") ?? "Item sem título";
  }
}

interface PendingValidationModalProps {
  open: boolean;
  onClose: () => void;
  professors: Professor[];
  linhasPesquisa: { id: string; nome: string }[];
  statsProfessorId: string;
  statsLinhaPesquisaId: string;
  breakdown?: Record<string, number>;
  onReview: (professorId: string, tab: EntityTab) => void;
  onGoToValidation: () => void;
}

export function PendingValidationModal({
  open,
  onClose,
  professors,
  linhasPesquisa,
  statsProfessorId,
  statsLinhaPesquisaId,
  breakdown,
  onReview,
  onGoToValidation,
}: PendingValidationModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PendingPayload | null>(null);

  const professorNameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const p of professors) map.set(p.id, p.nome_completo);
    return map;
  }, [professors]);

  const linhaFilterNome = useMemo(() => {
    if (statsLinhaPesquisaId === "todas") return null;
    return linhasPesquisa.find((l) => l.id === statsLinhaPesquisaId)?.nome ?? null;
  }, [statsLinhaPesquisaId, linhasPesquisa]);

  const professorAllowed = useMemo(() => {
    if (!linhaFilterNome) return null;
    return new Set(
      professors.filter((p) => p.linha === linhaFilterNome).map((p) => p.id)
    );
  }, [professors, linhaFilterNome]);

  useEffect(() => {
    if (!open) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (statsProfessorId !== "todos") params.set("professor_id", statsProfessorId);

    const qs = params.toString();
    const url = qs ? `/validacao/pendentes?${qs}` : "/validacao/pendentes";
    const pendingKey = cacheKey(
      "validacao",
      "pendentes",
      statsProfessorId !== "todos" ? statsProfessorId : "all"
    );

    cachedJson(
      pendingKey,
      async () => {
        const res = await apiFetch(url);
        if (!res.ok) throw new Error("Não foi possível carregar a fila de validação");
        return res.json() as Promise<PendingPayload>;
      }
    )
      .then((payload) => {
        if (cancelled) return;
        setData(payload);
      })
      .catch((err: Error) => {
        if (cancelled) return;
        setError(err.message || "Erro ao carregar pendentes");
        setData(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [open, statsProfessorId]);

  const filteredGroups = useMemo(() => {
    if (!data) return [] as { key: EntityTab; items: Record<string, unknown>[] }[];

    const matchesProfessor = (profId: string | undefined) => {
      if (!profId) return false;
      if (professorAllowed && !professorAllowed.has(profId)) return false;
      return true;
    };

    return ENTITY_KEYS.map((key) => {
      const raw = (data[key] as Record<string, unknown>[] | undefined) ?? [];
      const items = sortByNewestFirst(
        raw.filter((item) =>
          matchesProfessor(item.professor_id as string | undefined)
        ),
        key
      );
      return { key, items };
    }).filter((g) => g.items.length > 0);
  }, [data, professorAllowed]);

  const totalCount = filteredGroups.reduce((n, g) => n + g.items.length, 0);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="pending-validation-title"
    >
      <div className="glow-card w-full max-w-3xl max-h-[85vh] flex flex-col rounded-xl border border-slate-200 bg-white shadow-2xl">
        <div className="flex items-start justify-between gap-4 p-5 border-b border-slate-200">
          <div>
            <h2 id="pending-validation-title" className="text-base font-bold text-slate-900">
              Fila de validação pendente
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              {statsProfessorId !== "todos"
                ? "Filtrado pelo docente selecionado em Estatísticas"
                : "Todos os docentes"}
              {linhaFilterNome ? ` · linha: ${linhaFilterNome}` : ""}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            aria-label="Fechar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {breakdown && Object.keys(breakdown).length > 0 && (
          <div className="px-5 pt-4 flex flex-wrap gap-2">
            {Object.entries(breakdown)
              .filter(([, n]) => n > 0)
              .map(([key, n]) => (
                <span
                  key={key}
                  className="text-[10px] px-2 py-1 rounded-full bg-amber-950/50 border border-amber-800/40 text-amber-200 font-semibold"
                >
                  {ENTITY_LABELS[key as EntityTab] ?? key}: {n}
                </span>
              ))}
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {loading && (
            <div className="flex flex-col items-center py-12 gap-3 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
              <span className="text-xs">Carregando itens pendentes...</span>
            </div>
          )}

          {!loading && error && (
            <div className="flex items-center gap-3 p-4 rounded-lg bg-rose-950/30 border border-rose-800/50 text-rose-200 text-sm">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              {error}
            </div>
          )}

          {!loading && !error && totalCount === 0 && (
            <p className="text-center text-sm text-slate-400 py-10">
              Nenhum item pendente com os filtros atuais.
            </p>
          )}

          {!loading &&
            !error &&
            filteredGroups.map(({ key, items }) => (
              <section key={key} className="space-y-2">
                <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  {ENTITY_LABELS[key]} ({items.length})
                </h3>
                <ul className="space-y-2">
                  {items.map((item) => {
                    const id = String(item.id ?? "");
                    const profId = String(item.professor_id ?? "");
                    const profName =
                      professorNameById.get(profId) ?? "Docente desconhecido";
                    return (
                      <li
                        key={id || `${key}-${profId}-${itemTitle(key, item)}`}
                        className="flex items-center justify-between gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50 hover:border-indigo-800/60 transition-colors"
                      >
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-slate-900 truncate">
                            {itemTitle(key, item)}
                          </p>
                          <p className="text-[11px] text-slate-500 mt-0.5 truncate">
                            {profName}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            if (profId) onReview(profId, key);
                          }}
                          disabled={!profId}
                          className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          Revisar
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </section>
            ))}
        </div>

        <div className="p-4 border-t border-slate-200 flex justify-between items-center text-xs text-slate-500">
          <span>{totalCount} item(ns) na fila</span>
          <button
            type="button"
            onClick={() => {
              onClose();
              onGoToValidation();
            }}
            className="text-indigo-400 hover:text-indigo-300 font-semibold"
          >
            Ir para aba Validação
          </button>
        </div>
      </div>
    </div>
  );
}
