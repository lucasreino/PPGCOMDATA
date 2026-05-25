"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { DocentesHeader } from "@/components/docentes/DocentesHeader";

export default function DocentesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-600 text-sm bg-slate-50">
        Carregando sessão...
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <DocentesHeader />
      <main className="flex-1 px-6 py-8">
        <div className="max-w-7xl mx-auto">{children}</div>
      </main>
    </div>
  );
}
