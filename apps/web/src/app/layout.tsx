import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";

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
      <body className="antialiased min-h-screen flex flex-col">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
