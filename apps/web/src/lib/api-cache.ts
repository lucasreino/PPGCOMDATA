import { apiFetch } from "@/lib/api";

/** Alinhado ao TTL do cache do dossiê/analytics na API (~120s). */
export const DEFAULT_CACHE_TTL_MS = 120_000;

type CacheEntry<T> = { data: T; expiresAt: number };

const store = new Map<string, CacheEntry<unknown>>();

export function cacheKey(...parts: (string | number | boolean | null | undefined)[]): string {
  return parts.map((p) => String(p ?? "")).join(":");
}

export function isCacheValid(key: string): boolean {
  const hit = store.get(key);
  return Boolean(hit && hit.expiresAt > Date.now());
}

export function invalidateCacheKey(key: string): void {
  store.delete(key);
}

/** Remove todas as entradas cuja chave começa com `prefix`. */
export function invalidateCachePrefix(prefix: string): void {
  for (const key of store.keys()) {
    if (key.startsWith(prefix)) store.delete(key);
  }
}

export async function cachedJson<T>(
  key: string,
  fetcher: () => Promise<T>,
  options?: { ttlMs?: number; force?: boolean }
): Promise<T> {
  const ttlMs = options?.ttlMs ?? DEFAULT_CACHE_TTL_MS;
  const now = Date.now();

  if (!options?.force) {
    const hit = store.get(key) as CacheEntry<T> | undefined;
    if (hit && hit.expiresAt > now) {
      return hit.data;
    }
  }

  const data = await fetcher();
  store.set(key, { data, expiresAt: now + ttlMs });
  return data;
}

export async function fetchJsonCached<T>(
  path: string,
  options?: { cacheKey?: string; ttlMs?: number; force?: boolean }
): Promise<T> {
  const key = options?.cacheKey ?? path;
  return cachedJson(
    key,
    async () => {
      const res = await apiFetch(path);
      if (!res.ok) {
        throw new Error(`Falha na requisição (${res.status})`);
      }
      return res.json() as Promise<T>;
    },
    options
  );
}

/** Após importação, reprocessamento ou edição que altera indicadores. */
export function invalidateProfessorCaches(profId: string): void {
  invalidateCacheKey(cacheKey("validacao", "pendentes", profId));
  invalidateCacheKey(cacheKey("professor", "resumo", profId));
  invalidateCacheKey(cacheKey("professor", "dados", profId));
  invalidateCacheKey(cacheKey("professor", "catalog", profId));
  invalidateCachePrefix("dossie:");
  invalidateCachePrefix("analytics:");
  invalidateCacheKey(cacheKey("professores", "list"));
  invalidateCacheKey(cacheKey("professores", "catalog"));
}
