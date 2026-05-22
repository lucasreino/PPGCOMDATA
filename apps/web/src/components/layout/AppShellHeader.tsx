"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import {
  BarChart2,
  BookOpen,
  CheckCircle2,
  LogOut,
  Menu,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import type { MainTab } from "@/lib/types";

export type AppNavSection = "operacao" | "docentes" | "dossie";

const OPERACAO_ITEMS: {
  id: MainTab;
  label: string;
  shortLabel: string;
  icon: typeof CheckCircle2;
}[] = [
  { id: "validacao", label: "Validação", shortLabel: "Validação", icon: CheckCircle2 },
  { id: "estatisticas", label: "Indicadores", shortLabel: "Indicadores", icon: BarChart2 },
  {
    id: "relatorios",
    label: "Relatório IA",
    shortLabel: "Relatório",
    icon: Sparkles,
  },
];

function operacaoHref(tab: MainTab, searchParams: URLSearchParams): string {
  const params = new URLSearchParams(searchParams.toString());
  params.set("view", tab);
  const qs = params.toString();
  return qs ? `/?${qs}` : `/?view=${tab}`;
}

function NavGroup({
  label,
  children,
  className = "",
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <span className="text-[9px] font-bold uppercase tracking-wider text-slate-600 px-1">
        {label}
      </span>
      <div className="flex flex-wrap items-center gap-1">{children}</div>
    </div>
  );
}

function navBtnClass(active: boolean) {
  return `flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${
    active
      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/10"
      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
  }`;
}

export function AppShellHeader({
  section,
  operacaoView = "validacao",
  onOperacaoViewChange,
  apiConnected,
}: {
  section: AppNavSection;
  operacaoView?: MainTab;
  onOperacaoViewChange?: (tab: MainTab) => void;
  apiConnected?: boolean;
}) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const onOperacao = section === "operacao";
  const onDocentes = section === "docentes" || pathname.startsWith("/docentes");
  const onDossie = section === "dossie" || pathname.startsWith("/dossie-apcn");

  const operacaoLinks = (
    <>
      {OPERACAO_ITEMS.map(({ id, label, shortLabel, icon: Icon }) => {
        const active = onOperacao && operacaoView === id;
        const className = navBtnClass(active);
        if (onOperacao && onOperacaoViewChange) {
          return (
            <button
              key={id}
              type="button"
              onClick={() => {
                onOperacaoViewChange(id);
                setMobileOpen(false);
              }}
              className={className}
            >
              <Icon className="w-3.5 h-3.5 shrink-0" />
              <span className="hidden xl:inline">{label}</span>
              <span className="xl:hidden">{shortLabel}</span>
            </button>
          );
        }
        return (
          <Link
            key={id}
            href={operacaoHref(id, searchParams)}
            onClick={() => setMobileOpen(false)}
            className={className}
          >
            <Icon className="w-3.5 h-3.5 shrink-0" />
            <span className="hidden xl:inline">{label}</span>
            <span className="xl:hidden">{shortLabel}</span>
          </Link>
        );
      })}
    </>
  );

  const desktopNav = (
    <nav className="hidden lg:flex items-end gap-5">
      <NavGroup label="Gestão de dados">{operacaoLinks}</NavGroup>
      <div className="w-px h-10 bg-slate-800 self-end mb-0.5" aria-hidden />
      <NavGroup label="Docentes">
        <Link
          href="/docentes"
          className={navBtnClass(onDocentes)}
        >
          <Users className="w-3.5 h-3.5 shrink-0" />
          Corpo docente
        </Link>
      </NavGroup>
      <div className="w-px h-10 bg-slate-800 self-end mb-0.5" aria-hidden />
      <NavGroup label="Institucional">
        <Link href="/dossie-apcn" className={navBtnClass(onDossie)}>
          <BookOpen className="w-3.5 h-3.5 shrink-0" />
          Dossiê APCN
        </Link>
      </NavGroup>
    </nav>
  );

  const mobileNav = mobileOpen && (
    <div className="lg:hidden border-t border-slate-800 pt-4 mt-4 space-y-4">
      <NavGroup label="Gestão de dados">{operacaoLinks}</NavGroup>
      <NavGroup label="Docentes">
        <Link href="/docentes" className={navBtnClass(onDocentes)} onClick={() => setMobileOpen(false)}>
          <Users className="w-3.5 h-3.5" />
          Corpo docente
        </Link>
      </NavGroup>
      <NavGroup label="Institucional">
        <Link href="/dossie-apcn" className={navBtnClass(onDossie)} onClick={() => setMobileOpen(false)}>
          <BookOpen className="w-3.5 h-3.5" />
          Dossiê APCN
        </Link>
      </NavGroup>
    </div>
  );

  return (
    <header className="no-print border-b border-[#1e293b] bg-[#0f172a]/80 backdrop-blur-md sticky top-0 z-40">
      <div className="px-4 sm:px-6 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link href="/" className="flex items-center gap-3 min-w-0 group">
            <div className="bg-indigo-600 p-2 rounded-lg text-white shadow-lg shadow-indigo-600/20 shrink-0">
              <BarChart2 className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h1 className="text-base sm:text-lg font-bold tracking-tight text-white truncate">
                PPGCOM<span className="text-indigo-400">DATA</span>
              </h1>
              <p className="text-[10px] text-slate-500 truncate group-hover:text-slate-400 transition-colors">
                {onDossie
                  ? "Dossiê institucional APCN"
                  : onDocentes
                    ? "Perfis do corpo docente"
                    : "Validação, indicadores e relatórios"}
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-2 sm:gap-3">
            {apiConnected !== undefined && (
              <div className="hidden sm:flex items-center gap-2 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-full text-[10px]">
                <span
                  className={`w-1.5 h-1.5 rounded-full ${apiConnected ? "bg-emerald-500" : "bg-amber-500"}`}
                />
                <span className="text-slate-400">
                  {apiConnected ? "API" : "Offline"}
                </span>
              </div>
            )}

            {user && (
              <span className="hidden md:inline text-[10px] text-slate-500 max-w-[120px] truncate">
                {user.name}
              </span>
            )}

            <button
              type="button"
              onClick={logout}
              className="hidden sm:flex items-center gap-1 text-[10px] text-slate-400 hover:text-rose-300 border border-slate-800 hover:border-rose-900/60 px-2.5 py-1.5 rounded-lg transition-colors"
              title="Sair"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sair
            </button>

            <button
              type="button"
              className="lg:hidden p-2 rounded-lg border border-slate-800 text-slate-400 hover:text-white"
              onClick={() => setMobileOpen((o) => !o)}
              aria-expanded={mobileOpen}
              aria-label={mobileOpen ? "Fechar menu" : "Abrir menu"}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {desktopNav}
        {mobileNav}
      </div>
    </header>
  );
}
