/** URLs de foto: primeiro /public/fotos (mesma origem), depois API. */

import { getApiBaseUrl } from "@/lib/api";

const NOME_SLUG: Record<string, string> = {
  "izani pibernat mustafa": "izani",
  "jose carlos messias santos franco": "jose-messias",
  "larissa leda fonseca rocha": "larissa",
  "marcelli alves da silva": "marcelli",
  "domingos alves de almeida": "domingos",
  "odlinari ramon nascimento da silva": "odlinari",
  "camilla quesada tavares": "camilla",
  "leila lima de sousa": "leila",
  "leticia conceicao martins cardoso": "leticia",
  "thaisa cristina bueno": "thaisa",
  "maria gislene carvalho fonseca": "maria-gislene",
  "thays assuncao reis": "thays",
  "michelly santos de carvalho": "michelly",
};

const EXTENSIONS = [".gif", ".jpg", ".jpeg", ".png", ".webp"];

function normalizeNome(nome: string): string {
  return nome
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

export function nomeToPhotoSlug(nome: string): string | null {
  const key = normalizeNome(nome);
  if (NOME_SLUG[key]) return NOME_SLUG[key];
  const parts = key.replace(/[^a-z0-9\s-]/g, "").split(/\s+/).filter(Boolean);
  if (parts.length >= 2 && ["jose", "maria"].includes(parts[0])) {
    return `${parts[0]}-${parts[1]}`;
  }
  return parts[0] || null;
}

/** Caminho relativo no Next (public/fotos). */
export function publicFotoPaths(slug: string): string[] {
  return EXTENSIONS.map((ext) => `/fotos/${slug}${ext}`);
}

export function professorPhotoAssetUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;

  // Já é caminho público do site
  if (path.startsWith("/fotos/")) return path;

  const apiBase = getApiBaseUrl().replace(/\/$/, "");
  const apiOrigin = apiBase.replace(/\/api\/v1$/i, "");

  if (path.startsWith("/api/")) {
    return `${apiOrigin}${path}`;
  }
  return `${apiBase}/fotos/${path.replace(/^\//, "")}`;
}

/** Extrai camilla.gif de /api/v1/fotos/camilla.gif */
export function fotoUrlToPublicPath(fotoUrl: string): string | null {
  const match = fotoUrl.match(/\/fotos\/([^/?#]+)$/i);
  return match ? `/fotos/${match[1]}` : null;
}

export function getProfessorPhotoCandidates(prof: {
  id: string;
  id_lattes?: string | null;
  foto_url?: string | null;
  nome_completo?: string;
}): string[] {
  const urls: string[] = [];
  const seen = new Set<string>();

  const add = (url: string) => {
    let u = url;
    if (url.startsWith("http://") || url.startsWith("https://")) {
      u = url;
    } else if (url.startsWith("/api/")) {
      u = professorPhotoAssetUrl(url);
    } else if (url.startsWith("/") && !url.startsWith("//")) {
      u = url;
    } else {
      u = professorPhotoAssetUrl(url);
    }
    if (u && !seen.has(u)) {
      seen.add(u);
      urls.push(u);
    }
  };

  if (prof.foto_url?.trim()) {
    const trimmed = prof.foto_url.trim();
    const publicPath = fotoUrlToPublicPath(trimmed);
    // API-hosted fotos exist only on the backend; /fotos/* in public is optional.
    if (publicPath && !trimmed.includes("/api/")) {
      add(publicPath);
      return urls;
    }
    add(trimmed);
    return urls;
  }

  const slug = prof.nome_completo ? nomeToPhotoSlug(prof.nome_completo) : null;
  if (slug) {
    add(`/fotos/${slug}.gif`);
  }

  return urls;
}

export function professorInitials(nome: string): string {
  const parts = nome.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function professorAvatarColor(seed: string): string {
  const palette = [
    "from-indigo-600 to-violet-700",
    "from-emerald-600 to-teal-700",
    "from-amber-600 to-orange-700",
    "from-rose-600 to-pink-700",
    "from-cyan-600 to-blue-700",
    "from-fuchsia-600 to-purple-700",
  ];
  let hash = 0;
  for (let i = 0; i < seed.length; i++) hash = (hash + seed.charCodeAt(i)) % 997;
  return palette[hash % palette.length];
}
