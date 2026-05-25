"use client";

import React, { useEffect, useMemo, useState } from "react";
import { X, UserPlus, Upload, ImageIcon, Loader2 } from "lucide-react";
import { apiFetch, getStoredToken, parseApiErrorDetail } from "@/lib/api";

export interface LinhaPesquisaOption {
  id: string;
  nome: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  linhasPesquisa: LinhaPesquisaOption[];
  onSuccess: (professorId: string, nome: string) => void;
}

const TIPOS_DOCENTE = [
  { value: "permanente", label: "Permanente" },
  { value: "colaborador", label: "Colaborador" },
  { value: "visitante", label: "Visitante" },
  { value: "externo", label: "Externo" },
];

const initialForm = {
  nome_completo: "",
  email: "",
  link_lattes: "",
  id_lattes: "",
  tipo_docente: "permanente",
  linha_pesquisa_id: "",
  grupo_pesquisa: "",
  tematicas: "",
};

export function NovoDocenteModal({ open, onClose, linhasPesquisa, onSuccess }: Props) {
  const [form, setForm] = useState(initialForm);
  const [xmlFile, setXmlFile] = useState<File | null>(null);
  const [fotoFile, setFotoFile] = useState<File | null>(null);
  const [fotoPreview, setFotoPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setForm(initialForm);
    setXmlFile(null);
    setFotoFile(null);
    setFotoPreview(null);
    setError(null);
    setSuccessMsg(null);
  }, [open]);

  useEffect(() => {
    if (!fotoPreview) return;
    return () => URL.revokeObjectURL(fotoPreview);
  }, [fotoPreview]);

  const linhaOptions = useMemo(
    () => linhasPesquisa.filter((l) => l.id && l.nome),
    [linhasPesquisa]
  );

  if (!open) return null;

  const setField = (key: keyof typeof form, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleFotoChange = (file: File | undefined) => {
    if (!file) return;
    setFotoFile(file);
    setFotoPreview(URL.createObjectURL(file));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!form.nome_completo.trim()) {
      setError("Informe o nome completo do docente.");
      return;
    }

    const token = getStoredToken();
    if (!token) {
      setError("Sessão expirada. Faça login novamente.");
      return;
    }

    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("nome_completo", form.nome_completo.trim());
      if (form.email.trim()) fd.append("email", form.email.trim());
      if (form.link_lattes.trim()) fd.append("link_lattes", form.link_lattes.trim());
      if (form.id_lattes.trim()) fd.append("id_lattes", form.id_lattes.trim());
      fd.append("tipo_docente", form.tipo_docente);
      if (form.linha_pesquisa_id) fd.append("linha_pesquisa_id", form.linha_pesquisa_id);
      if (form.grupo_pesquisa.trim()) fd.append("grupo_pesquisa", form.grupo_pesquisa.trim());
      if (form.tematicas.trim()) fd.append("tematicas", form.tematicas.trim());
      if (xmlFile) fd.append("xml_curriculo", xmlFile);
      if (fotoFile) fd.append("foto", fotoFile);

      const res = await apiFetch("/professores/cadastro", {
        method: "POST",
        body: fd,
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(parseApiErrorDetail(data.detail, "Não foi possível cadastrar o docente."));
      }

      setSuccessMsg(data.mensagem || "Docente cadastrado.");
      onSuccess(data.professor_id, data.nome_completo || form.nome_completo);
      setTimeout(() => onClose(), 1200);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao cadastrar docente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="novo-docente-title"
    >
      <div className="glow-card w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl border border-slate-700 shadow-2xl">
        <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-4 border-b border-slate-800 bg-slate-950/95">
          <div className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-indigo-400" />
            <h2 id="novo-docente-title" className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Novo docente
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            aria-label="Fechar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          <section className="space-y-3">
            <h3 className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
              Identificação
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <label className="md:col-span-2 space-y-1">
                <span className="text-xs text-slate-400">Nome completo *</span>
                <input
                  required
                  value={form.nome_completo}
                  onChange={(e) => setField("nome_completo", e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100"
                  placeholder="Ex.: Maria Silva Santos"
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-slate-400">E-mail institucional</span>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setField("email", e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100"
                  placeholder="nome@ufma.br"
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-slate-400">Tipo de vínculo</span>
                <select
                  value={form.tipo_docente}
                  onChange={(e) => setField("tipo_docente", e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100"
                >
                  {TIPOS_DOCENTE.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-1">
                <span className="text-xs text-slate-400">Link Lattes</span>
                <input
                  value={form.link_lattes}
                  onChange={(e) => setField("link_lattes", e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100"
                  placeholder="http://lattes.cnpq.br/..."
                />
              </label>
              <label className="space-y-1">
                <span className="text-xs text-slate-400">ID Lattes (CNPq)</span>
                <input
                  value={form.id_lattes}
                  onChange={(e) => setField("id_lattes", e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100"
                  placeholder="Somente números"
                />
              </label>
              <label className="md:col-span-2 space-y-1">
                <span className="text-xs text-slate-400">Linha de pesquisa</span>
                <select
                  value={form.linha_pesquisa_id}
                  onChange={(e) => setField("linha_pesquisa_id", e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100"
                >
                  <option value="">— Selecionar —</option>
                  {linhaOptions.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.nome}
                    </option>
                  ))}
                </select>
              </label>
              <label className="md:col-span-2 space-y-1">
                <span className="text-xs text-slate-400">Grupo de pesquisa</span>
                <input
                  value={form.grupo_pesquisa}
                  onChange={(e) => setField("grupo_pesquisa", e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100"
                />
              </label>
              <label className="md:col-span-2 space-y-1">
                <span className="text-xs text-slate-400">Temáticas de pesquisa</span>
                <textarea
                  rows={2}
                  value={form.tematicas}
                  onChange={(e) => setField("tematicas", e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100 resize-y"
                />
              </label>
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
              Currículo e foto
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <label className="flex flex-col items-center justify-center gap-2 p-4 border-2 border-dashed border-slate-700 rounded-xl cursor-pointer hover:border-indigo-700 hover:bg-indigo-950/20 transition-colors min-h-[120px]">
                <Upload className="w-6 h-6 text-indigo-400" />
                <span className="text-xs font-semibold text-slate-300 text-center">
                  {xmlFile ? xmlFile.name : "XML do Lattes (.xml)"}
                </span>
                <span className="text-[10px] text-slate-500 text-center">
                  Exporte no portal CNPq e envie o arquivo
                </span>
                <input
                  type="file"
                  accept=".xml,application/xml,text/xml"
                  className="hidden"
                  onChange={(e) => setXmlFile(e.target.files?.[0] ?? null)}
                />
              </label>

              <label className="flex flex-col items-center justify-center gap-2 p-4 border-2 border-dashed border-slate-700 rounded-xl cursor-pointer hover:border-indigo-700 hover:bg-indigo-950/20 transition-colors min-h-[120px]">
                {fotoPreview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={fotoPreview}
                    alt="Pré-visualização"
                    className="w-16 h-16 rounded-full object-cover border border-slate-600"
                  />
                ) : (
                  <ImageIcon className="w-6 h-6 text-indigo-400" />
                )}
                <span className="text-xs font-semibold text-slate-300 text-center">
                  {fotoFile ? fotoFile.name : "Foto do docente"}
                </span>
                <span className="text-[10px] text-slate-500">JPG, PNG, WEBP ou GIF</span>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  className="hidden"
                  onChange={(e) => handleFotoChange(e.target.files?.[0])}
                />
              </label>
            </div>
          </section>

          {error && (
            <p className="text-xs text-rose-400 bg-rose-950/40 border border-rose-900/50 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
          {successMsg && (
            <p className="text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-900/50 rounded-lg px-3 py-2">
              {successMsg}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Cadastrando…
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  Cadastrar docente
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
