import type { EntityTab } from "@/lib/types";

export const VALIDATION_TABS: EntityTab[] = [
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

export function tabLabel(tab: EntityTab): string {
  const labels: Record<EntityTab, string> = {
    projetos: "projetos",
    eventos: "eventos",
    producoes: "produções",
    financiamentos: "financiamentos",
    orientacoes: "orientações",
    formacoes_academicas: "formação",
    producoes_tecnicas: "prod. técnica",
    premios: "prêmios",
    grupos_pesquisa: "grupos",
  };
  return labels[tab];
}
