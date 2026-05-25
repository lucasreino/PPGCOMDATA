"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { SplineHeroBackground } from "@/components/login/SplineHeroBackground";

export default function LoginPage() {
  const router = useRouter();
  const { user, login, loading: authLoading } = useAuth();

  useEffect(() => {
    if (!authLoading && user) {
      router.replace("/");
    }
  }, [authLoading, user, router]);
  const [email, setEmail] = useState("admin@ppgcom.edu");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao entrar.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-6 bg-hero-bg overflow-hidden">
      <SplineHeroBackground />
      <div className="relative z-10 w-full max-w-md login-sentinel-card rounded-2xl p-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="bg-sentinel-primary p-2 rounded-lg text-sentinel-primary-foreground">
            <BarChart2 className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-sentinel-foreground tracking-tight">
              PPGCOM<span className="text-sentinel-primary">DATA</span>
            </h1>
            <p className="text-xs text-sentinel-muted-foreground">
              Acesso ao painel institucional
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-sentinel-muted-foreground font-medium uppercase tracking-widest">
              E-mail
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full bg-sentinel-muted border border-sentinel-input rounded-lg px-3 py-2 text-sm text-sentinel-foreground placeholder:text-sentinel-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-sentinel-primary/40 focus:border-sentinel-primary/50 transition-shadow"
              required
            />
          </div>
          <div>
            <label className="text-xs text-sentinel-muted-foreground font-medium uppercase tracking-widest">
              Senha
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full bg-sentinel-muted border border-sentinel-input rounded-lg px-3 py-2 text-sm text-sentinel-foreground placeholder:text-sentinel-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-sentinel-primary/40 focus:border-sentinel-primary/50 transition-shadow"
              required
            />
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-950/30 border border-red-900/50 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting || authLoading}
            className="w-full py-3 bg-sentinel-primary hover:brightness-110 disabled:opacity-50 text-sentinel-primary-foreground text-sm font-bold rounded-sm transition-all active:scale-[0.97]"
          >
            {submitting ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p className="mt-6 text-[11px] text-sentinel-muted-foreground/60 text-center font-light">
          Primeiro acesso? Execute{" "}
          <code className="text-sentinel-primary/90">python -m app.create_admin</code> na API.
        </p>
      </div>
    </div>
  );
}
