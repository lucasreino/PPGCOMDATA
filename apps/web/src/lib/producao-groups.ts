import type { Producao } from "@/lib/types";
import { sortByNewestFirst } from "@/lib/sort-entities";

export const PRODUCAO_TIPO_ORDER = [
  "artigo",
  "livro",
  "capitulo",
  "anais",
  "resumo",
  "tecnica",
  "outra",
] as const;

const PRODUCAO_TIPO_ALIASES: Record<string, string> = {
  artigos: "artigo",
  article: "artigo",
  artigo_periodico: "artigo",
  livros: "livro",
  book: "livro",
  capitulos: "capitulo",
  "capítulo": "capitulo",
  capitulo_de_livro: "capitulo",
  capitulo_livro: "capitulo",
  trabalho_em_evento: "anais",
  trabalhos_em_eventos: "anais",
  resumo_expandido: "resumo",
  producao_tecnica: "tecnica",
  outro: "outra",
  outras: "outra",
};

export const PRODUCAO_TIPO_LABELS: Record<string, string> = {
  artigo: "Artigos",
  livro: "Livros",
  capitulo: "Capítulos de livros",
  anais: "Anais",
  resumo: "Resumos",
  tecnica: "Produção técnica",
  outra: "Outras produções",
};

export function normalizeProducaoTipo(tipo: string): string {
  const raw = (tipo || "outra").trim().toLowerCase();
  if (PRODUCAO_TIPO_ALIASES[raw]) return PRODUCAO_TIPO_ALIASES[raw];
  if ((PRODUCAO_TIPO_ORDER as readonly string[]).includes(raw)) return raw;
  if (raw.includes("artigo")) return "artigo";
  if (raw.includes("capit")) return "capitulo";
  if (raw.includes("livro")) return "livro";
  if (raw.includes("anais") || raw.includes("evento")) return "anais";
  if (raw.includes("resumo")) return "resumo";
  return "outra";
}

export function labelProducaoTipo(tipo: string): string {
  return PRODUCAO_TIPO_LABELS[tipo] || tipo.replace(/_/g, " ");
}

export function groupProducoesByTipo(
  items: Producao[]
): { tipo: string; label: string; items: Producao[] }[] {
  const map = new Map<string, Producao[]>();
  for (const item of items) {
    const key = normalizeProducaoTipo(item.tipo || "outra");
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(item);
  }

  const seen = new Set<string>();
  const groups: { tipo: string; label: string; items: Producao[] }[] = [];

  for (const tipo of PRODUCAO_TIPO_ORDER) {
    const list = map.get(tipo);
    if (list?.length) {
      groups.push({
        tipo,
        label: labelProducaoTipo(tipo),
        items: sortByNewestFirst(list, "producoes"),
      });
      seen.add(tipo);
    }
  }

  for (const [tipo, list] of Array.from(map.entries())) {
    if (!seen.has(tipo) && list.length) {
      groups.push({
        tipo,
        label: labelProducaoTipo(tipo),
        items: sortByNewestFirst(list, "producoes"),
      });
    }
  }

  return groups;
}
