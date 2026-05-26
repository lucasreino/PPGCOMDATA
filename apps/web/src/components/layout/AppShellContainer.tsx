import type { ReactNode } from "react";

/** Largura máxima alinhada ao miolo das páginas (Dossiê, validação, docentes). */
export const APP_SHELL_MAX_WIDTH_CLASS = "max-w-[1400px]";

export function appShellContainerClass(extra = "") {
  return `${APP_SHELL_MAX_WIDTH_CLASS} mx-auto w-full px-4 sm:px-6 ${extra}`.trim();
}

export function AppShellContainer({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={appShellContainerClass(className)}>{children}</div>;
}
