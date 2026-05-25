"use client";

import type { ProfessorResumo } from "@/lib/types";
import { Award, BookOpen, GraduationCap } from "lucide-react";

export function ResumoAcademicoCard({ resumo }: { resumo: ProfessorResumo | null }) {
  if (!resumo) return null;

  return (
    <div className="glow-card rounded-xl p-4 border border-indigo-200 bg-indigo-50/60 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
      <div>
        <span className="text-[9px] text-slate-500 uppercase font-bold flex items-center gap-1">
          <GraduationCap className="w-3 h-3" /> Titulação
        </span>
        <p className="text-slate-800 font-semibold mt-1 capitalize">
          {resumo.titulacao_maxima || "—"}
        </p>
      </div>
      <div>
        <span className="text-[9px] text-slate-500 uppercase font-bold flex items-center gap-1">
          <Award className="w-3 h-3" /> Orientações
        </span>
        <p className="text-slate-800 font-semibold mt-1">
          {resumo.total_orientacoes} total ({resumo.orientacoes_em_andamento} ativas)
        </p>
      </div>
      <div>
        <span className="text-[9px] text-slate-500 uppercase font-bold">Últimos 5 anos</span>
        <p className="text-slate-800 font-semibold mt-1">{resumo.orientacoes_ultimos_5_anos}</p>
      </div>
      <div>
        <span className="text-[9px] text-slate-500 uppercase font-bold flex items-center gap-1">
          <BookOpen className="w-3 h-3" /> Formações
        </span>
        <p className="text-slate-800 font-semibold mt-1">{resumo.total_formacoes} registros</p>
      </div>
    </div>
  );
}
