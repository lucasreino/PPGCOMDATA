/** Ordena registros do mais recente para o mais antigo (espelha a API). */

type Rec = Record<string, unknown>;

function ts(value: unknown): number {
  if (!value) return 0;
  const t = new Date(String(value)).getTime();
  return Number.isFinite(t) ? t : 0;
}

function dateOrd(value: unknown): number {
  if (!value) return 0;
  const d = new Date(String(value));
  if (Number.isNaN(d.getTime())) return 0;
  return d.getFullYear() * 10_000 + (d.getMonth() + 1) * 100 + d.getDate();
}

function num(value: unknown): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

export function entityRecencyKey(entityKey: string, item: Rec): [number, number] {
  const tieTs = Math.max(ts(item.created_at), ts(item.updated_at));
  const currentYear = new Date().getFullYear();

  let primary = 0;

  if (entityKey === "projetos") {
    const start = num(item.ano_inicio);
    const endRaw = item.ano_fim;
    const year =
      endRaw != null && endRaw !== ""
        ? num(endRaw)
        : start
          ? currentYear
          : 0;
    primary = Math.max(year, start);
  } else if (
    entityKey === "eventos" ||
    entityKey === "producoes" ||
    entityKey === "producoes_tecnicas" ||
    entityKey === "premios"
  ) {
    primary = num(item.ano);
  } else if (entityKey === "financiamentos") {
    if (item.vigencia_fim) primary = dateOrd(item.vigencia_fim);
    else if (item.ano != null && item.ano !== "") primary = num(item.ano);
    else if (item.vigencia_inicio) primary = dateOrd(item.vigencia_inicio);
  } else if (entityKey === "orientacoes") {
    const conclusao = num(item.ano_conclusao);
    const inicio = num(item.ano_inicio);
    primary = Math.max(conclusao, inicio);
    if (!conclusao && String(item.status || "").toLowerCase() === "em_andamento") {
      primary = Math.max(primary, inicio || currentYear);
    }
  } else if (entityKey === "formacoes_academicas") {
    primary = num(item.ano_fim) || num(item.ano_inicio);
  } else if (entityKey === "bancas") {
    primary = num(item.ano);
  } else if (entityKey === "perfis_lattes") {
    primary = dateOrd(item.data_ultima_atualizacao);
  } else if (entityKey === "lacunas") {
    primary = dateOrd(item.prazo);
  }

  return [primary, tieTs];
}

export function sortByNewestFirst<T>(
  items: T[],
  entityKey: string
): T[] {
  return [...items].sort((a, b) => {
    const [pa, ta] = entityRecencyKey(entityKey, a as Rec);
    const [pb, tb] = entityRecencyKey(entityKey, b as Rec);
    if (pb !== pa) return pb - pa;
    return tb - ta;
  });
}

const PAYLOAD_KEYS = [
  "projetos",
  "eventos",
  "producoes",
  "financiamentos",
  "orientacoes",
  "formacoes_academicas",
  "bancas",
  "producoes_tecnicas",
  "premios",
  "grupos_pesquisa",
  "lacunas",
] as const;

/** Ordena listas em payload de `/validacao/pendentes` ou `/professores/{id}/dados`. */
export function sortEntityPayload<T extends Rec>(payload: T): T {
  const out = { ...payload };
  for (const key of PAYLOAD_KEYS) {
    const list = out[key];
    if (Array.isArray(list)) {
      (out as Rec)[key] = sortByNewestFirst(list as Rec[], key);
    }
  }
  return out;
}
