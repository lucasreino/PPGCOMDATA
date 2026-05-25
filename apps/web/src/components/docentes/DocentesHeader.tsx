"use client";

import { Suspense } from "react";
import { AppShellHeader } from "@/components/layout/AppShellHeader";

function HeaderFallback() {
  return (
    <header className="border-b border-slate-200 bg-white h-[72px] animate-pulse" />
  );
}

/** @deprecated Use AppShellHeader via layout; mantido para imports legados. */
export function DocentesHeader() {
  return (
    <Suspense fallback={<HeaderFallback />}>
      <AppShellHeader section="docentes" />
    </Suspense>
  );
}
