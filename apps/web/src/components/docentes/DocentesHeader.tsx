"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart2, Grid3X3, LogOut, Settings } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export function DocentesHeader() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const onDocentes = pathname.startsWith("/docentes");

  return (
    <header className="border-b border-[#1e293b] bg-[#0f172a]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-600 p-2 rounded-lg text-white shadow-lg shadow-indigo-600/20">
            <BarChart2 className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">PPGCOMDATA</h1>
            <p className="text-[10px] text-slate-400 uppercase tracking-wider">
              Corpo docente
            </p>
          </div>
        </div>

        <nav className="flex items-center gap-1 text-xs font-semibold">
          <Link
            href="/docentes"
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
              onDocentes
                ? "bg-indigo-950/60 text-indigo-300 border border-indigo-800/50"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Grid3X3 className="w-4 h-4" />
            Docentes
          </Link>
          <Link
            href="/"
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
              !onDocentes
                ? "bg-indigo-950/60 text-indigo-300 border border-indigo-800/50"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Settings className="w-4 h-4" />
            Validação
          </Link>
        </nav>

        <div className="flex items-center gap-3 text-xs text-slate-400">
          {user && <span className="hidden sm:inline">{user.name}</span>}
          <button
            type="button"
            onClick={logout}
            className="flex items-center gap-1 px-2 py-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-rose-300 transition-colors"
            title="Sair"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
