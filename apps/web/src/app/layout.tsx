import type { Metadata } from "next";
import { Suspense } from "react";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "PPGCOMDATA — Gestão & Indicadores Docentes",
  description: "Sistema inteligente de extração e validação de indicadores curriculares do PPGCOM",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className={`${plusJakarta.variable} antialiased min-h-screen flex flex-col font-sans`}>
        <AuthProvider>
          <Suspense
            fallback={
              <div className="min-h-screen flex items-center justify-center text-slate-600 text-sm bg-slate-50">
                Carregando...
              </div>
            }
          >
            {children}
          </Suspense>
        </AuthProvider>
      </body>
    </html>
  );
}
