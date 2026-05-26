"use client";

import { X } from "lucide-react";
import type { KpiDetailState } from "@/lib/dossie-kpi-detail";
import { cellValue } from "@/lib/dossie-kpi-detail";

export function KpiDetailModal({
  detail,
  onClose,
}: {
  detail: KpiDetailState | null;
  onClose: () => void;
}) {
  if (!detail) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="kpi-detail-title"
    >
      <div className="glow-card w-full max-w-4xl max-h-[85vh] flex flex-col rounded-xl border border-slate-200 bg-white shadow-2xl">
        <div className="flex items-start justify-between gap-4 p-5 border-b border-slate-200">
          <div>
            <h2 id="kpi-detail-title" className="text-base font-bold text-slate-900">
              {detail.title}
            </h2>
            {detail.subtitle && (
              <p className="text-xs text-slate-500 mt-1">{detail.subtitle}</p>
            )}
            <p className="text-[10px] text-indigo-600 font-semibold mt-2">
              {detail.rows.length} item(ns)
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100"
            aria-label="Fechar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-auto p-4">
          {detail.rows.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-12">
              {detail.emptyMessage ?? "Nenhum registro para exibir."}
            </p>
          ) : (
            <table className="w-full text-xs min-w-[500px]">
              <thead className="bg-slate-100 text-slate-600 uppercase text-[10px] sticky top-0">
                <tr>
                  {detail.columns.map((col) => (
                    <th
                      key={col.key}
                      className={`p-2 ${
                        col.align === "right"
                          ? "text-right"
                          : col.align === "center"
                            ? "text-center"
                            : "text-left"
                      }`}
                    >
                      {col.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {detail.rows.map((row, i) => (
                  <tr
                    key={String(row.id ?? row.professor_id ?? i)}
                    className="border-t border-slate-200 hover:bg-slate-50"
                  >
                    {detail.columns.map((col) => (
                      <td
                        key={col.key}
                        className={`p-2 text-slate-800 ${
                          col.align === "right"
                            ? "text-right"
                            : col.align === "center"
                              ? "text-center"
                              : "text-left"
                        } ${col.mono ? "font-mono text-[10px]" : ""} ${
                          col.truncate ? "max-w-[220px] truncate" : ""
                        }`}
                        title={col.truncate ? cellValue(col, row) : undefined}
                      >
                        {cellValue(col, row)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="p-3 border-t border-slate-200 text-[10px] text-slate-500 text-center">
          Clique fora ou no ✕ para fechar
        </div>
      </div>
    </div>
  );
}
