const PRINT_BODY_CLASS = "ppgcomdata-printing-qualis";

/** Imprime o painel #artigos-qualis-print-root via diálogo nativo do navegador. */
export function printArtigosQualisInPage(): boolean {
  if (typeof window === "undefined") return false;

  const root = document.getElementById("artigos-qualis-print-root");
  if (!root) {
    alert("Abra o painel de artigos Qualis e aguarde o carregamento antes de imprimir.");
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
