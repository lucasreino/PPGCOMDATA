const PRINT_BODY_CLASS = "ppgcomdata-printing-orientacoes";

/** Imprime o painel #orientacoes-print-root via diálogo nativo do navegador. */
export function printOrientacoesInPage(): boolean {
  if (typeof window === "undefined") return false;

  const root = document.getElementById("orientacoes-print-root");
  if (!root) {
    alert("Abra o painel de orientações e aguarde o carregamento antes de imprimir.");
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
