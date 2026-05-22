"use client";

import type { ComponentType } from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, Calendar, GraduationCap, FolderKanban } from "lucide-react";
import type { ProfessorCatalog } from "@/lib/types";
import { ProfessorAvatar } from "./ProfessorAvatar";

export function ProfessorCard({ prof }: { prof: ProfessorCatalog }) {
  const linha = prof.linha_pesquisa?.nome ?? "Linha não informada";
  const tipo =
    prof.tipo_docente.charAt(0).toUpperCase() + prof.tipo_docente.slice(1);

  return (
    <Link
      href={`/docentes/${prof.id}`}
      className="glow-card group rounded-2xl p-5 border border-slate-800 hover:border-indigo-700/60 hover:shadow-lg hover:shadow-indigo-950/30 transition-all duration-300 flex flex-col"
    >
      <div className="flex flex-col items-center text-center">
        <ProfessorAvatar
          nome={prof.nome_completo}
          id={prof.id}
          id_lattes={prof.id_lattes}
          foto_url={prof.foto_url}
          size="lg"
          className="mb-4 group-hover:ring-indigo-600/50 transition-all"
        />
        <h2 className="text-sm font-bold text-slate-100 leading-snug line-clamp-2">
          {prof.nome_completo}
        </h2>
        <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{linha}</p>
        <span className="text-[10px] mt-2 px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 uppercase font-semibold tracking-wider">
          {tipo}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-800/80 text-[10px]">
        <Stat icon={FolderKanban} label="Projetos" value={prof.total_projetos} />
        <Stat icon={BookOpen} label="Produções" value={prof.total_producoes} />
        <Stat icon={GraduationCap} label="Orientações" value={prof.total_orientacoes} />
        <Stat icon={Calendar} label="Eventos" value={prof.total_eventos} />
      </div>

      <div className="mt-4 flex items-center justify-center gap-1 text-[11px] font-semibold text-indigo-400 group-hover:text-indigo-300">
        Ver perfil completo
        <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
      </div>
    </Link>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: number;
}) {
  return (
    <div className="bg-slate-900/50 rounded-lg px-2 py-1.5 border border-slate-850">
      <span className="text-slate-500 flex items-center gap-1">
        <Icon className="w-3 h-3" />
        {label}
      </span>
      <span className="text-slate-200 font-bold block mt-0.5">{value}</span>
    </div>
  );
}
