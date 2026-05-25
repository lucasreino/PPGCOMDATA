"use client";

import { useMemo, useState } from "react";
import {
  getProfessorPhotoCandidates,
  professorAvatarColor,
  professorInitials,
} from "@/lib/professor-photo";

type Size = "sm" | "md" | "lg" | "xl";

const sizeClasses: Record<Size, string> = {
  sm: "w-12 h-12 text-sm",
  md: "w-16 h-16 text-base",
  lg: "w-24 h-24 text-xl",
  xl: "w-32 h-32 text-2xl",
};

export function ProfessorAvatar({
  nome,
  id,
  id_lattes,
  foto_url,
  size = "md",
  className = "",
}: {
  nome: string;
  id: string;
  id_lattes?: string | null;
  foto_url?: string | null;
  size?: Size;
  className?: string;
}) {
  const candidates = useMemo(
    () => getProfessorPhotoCandidates({ id, id_lattes, foto_url, nome_completo: nome }),
    [id, id_lattes, foto_url, nome]
  );
  const [idx, setIdx] = useState(0);
  const src = idx < candidates.length ? candidates[idx] : null;
  const initials = professorInitials(nome);
  const gradient = professorAvatarColor(id);

  return (
    <div
      className={`relative rounded-full overflow-hidden shrink-0 ring-2 ring-slate-200 ${sizeClasses[size]} ${className}`}
    >
      {src ? (
        <img
          src={src}
          alt={nome}
          loading="lazy"
          decoding="async"
          className="w-full h-full object-cover"
          onError={() => setIdx((i) => i + 1)}
        />
      ) : (
        <div
          className={`w-full h-full flex items-center justify-center font-bold text-white bg-gradient-to-br ${gradient}`}
        >
          {initials}
        </div>
      )}
    </div>
  );
}
