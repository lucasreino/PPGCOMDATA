/** Impressão do relatório na própria página (sem pop-up). */

export interface ReportPrintMeta {
  title?: string;
  modelo?: string;
  docente?: string;
  linha?: string;
  periodo?: string;
  geradoEm?: string;
}

const PRINT_BODY_CLASS = "ppgcomdata-printing-report";

/** Imprime o conteúdo de #report-print-root via diálogo nativo do navegador. */
export function printReportInPage(): boolean {
  if (typeof window === "undefined") return false;

  const root = document.getElementById("report-print-root");
  if (!root) {
    alert("Gere um relatório antes de imprimir.");
    return false;
  }

  document.body.classList.add(PRINT_BODY_CLASS);

  const cleanup = () => {
    document.body.classList.remove(PRINT_BODY_CLASS);
    window.removeEventListener("afterprint", cleanup);
  };
  window.addEventListener("afterprint", cleanup);

  requestAnimationFrame(() => {
    window.print();
  });

  return true;
}

/** @deprecated Use printReportInPage */
export function openReportPrintWindow(
  _markdown?: string,
  _meta?: ReportPrintMeta
): boolean {
  return printReportInPage();
}
