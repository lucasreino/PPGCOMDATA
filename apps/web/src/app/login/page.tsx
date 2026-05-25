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
    <div className="relative min-h-screen flex items-center justify-center p-6 bg-slate-100 overflow-hidden">
      <SplineHeroBackground />
      <div className="relative z-10 w-full max-w-md glow-card rounded-2xl p-8 border border-slate-200 shadow-lg">
        <div className="flex items-center gap-3 mb-8">
          <div className="bg-indigo-600 p-2 rounded-lg text-white">
            <BarChart2 className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">PPGCOMDATA</h1>
            <p className="text-xs text-slate-600">Acesso ao painel institucional</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-slate-600 font-semibold uppercase tracking-wider">
              E-mail
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field mt-1"
              required
            />
          </div>
          <div>
            <label className="text-xs text-slate-600 font-semibold uppercase tracking-wider">
              Senha
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field mt-1"
              required
            />
          </div>

          {error && (
            <p className="text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting || authLoading}
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-bold rounded-lg transition-colors active:scale-[0.97]"
          >
            {submitting ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p className="mt-6 text-[11px] text-slate-500 text-center">
          Primeiro acesso? Execute{" "}
          <code className="text-indigo-700 bg-indigo-50 px-1 rounded">python -m app.create_admin</code> na API.
        </p>
      </div>
    </div>
  );
}
