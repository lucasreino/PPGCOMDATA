import type { Orientacao } from "@/lib/types";
import { sortByNewestFirst } from "@/lib/sort-entities";

export const ORIENTACAO_TIPO_ORDER = [
  "doutorado",
  "mestrado",
  "pos_doutorado",
  "ic",
  "tcc",
  "outra",
] as const;

export const ORIENTACAO_TIPO_LABELS: Record<string, string> = {
  doutorado: "Doutorado",
  mestrado: "Mestrado",
  pos_doutorado: "Pós-doutorado",
  ic: "Iniciação científica",
  tcc: "TCC / Graduação",
  outra: "Outras orientações",
};

export function labelOrientacaoTipo(tipo: string): string {
  return ORIENTACAO_TIPO_LABELS[tipo] || tipo.replace(/_/g, " ");
}

export function groupOrientacoesByTipo(
  items: Orientacao[]
): { tipo: string; label: string; items: Orientacao[] }[] {
  const map = new Map<string, Orientacao[]>();
  for (const item of items) {
    const key = (item.tipo || "outra").toLowerCase();
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(item);
  }

  const seen = new Set<string>();
  const groups: { tipo: string; label: string; items: Orientacao[] }[] = [];

  for (const tipo of ORIENTACAO_TIPO_ORDER) {
    const list = map.get(tipo);
    if (list?.length) {
      groups.push({
        tipo,
        label: labelOrientacaoTipo(tipo),
        items: sortByNewestFirst(list, "orientacoes"),
      });
      seen.add(tipo);
    }
  }

  for (const [tipo, list] of Array.from(map.entries())) {
    if (!seen.has(tipo) && list.length) {
      groups.push({
        tipo,
        label: labelOrientacaoTipo(tipo),
        items: sortByNewestFirst(list, "orientacoes"),
      });
    }
  }

  return groups;
}
