"use client";

function formatHIndex(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

export function ProducaoIndicadores({
  qualis,
  journal_h_index,
  scholar_citations,
  scholar_h5_index,
  scholar_metrics_year,
  compact = false,
}: {
  qualis?: string | null;
  journal_h_index?: number | null;
  scholar_citations?: number | null;
  scholar_h5_index?: number | null;
  scholar_metrics_year?: number | null;
  /** Menos badges secundários (só Qualis + h-index revista). */
  compact?: boolean;
}) {
  const hasQualis = Boolean(qualis?.trim());
  const hasH = journal_h_index != null && !Number.isNaN(journal_h_index);
  const hasCit = scholar_citations != null;
  const hasH5 = scholar_h5_index != null;

  if (!hasQualis && !hasH && !hasCit && !hasH5) {
    return null;
  }

  const chip = compact
    ? "px-1.5 py-0.5 rounded text-[10px] font-bold"
    : "px-2 py-0.5 rounded-md text-[10px] font-bold";

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {hasQualis && (
        <span
          className={`${chip} bg-indigo-100 text-indigo-800 border border-indigo-200`}
          title="Estrato Qualis"
        >
          Qualis {qualis}
        </span>
      )}
      {hasH && (
        <span
          className={`${chip} bg-sky-100 text-sky-900 border border-sky-200`}
          title="h-index da revista (OpenAlex)"
        >
          h-index {formatHIndex(journal_h_index!)}
        </span>
      )}
      {!compact && hasCit && (
        <span
          className={`${chip} bg-amber-100 text-amber-900 border border-amber-200`}
          title="Citações do artigo no Google Acadêmico"
        >
          {scholar_citations} cit.
        </span>
      )}
      {!compact && hasH5 && (
        <span
          className={`${chip} bg-emerald-100 text-emerald-900 border border-emerald-200`}
          title="Google Scholar Metrics (h5-index da revista)"
        >
          h5 {scholar_h5_index}
          {scholar_metrics_year != null ? ` · ${scholar_metrics_year}` : ""}
        </span>
      )}
    </div>
  );
}
