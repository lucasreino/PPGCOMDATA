"use client";

import React, { useState } from "react";
import {
  Check,
  Edit2,
  Trash2,
  FileText,
  Info,
  Eye,
  EyeOff,
} from "lucide-react";

export function ConfidenceBadge({ level }: { level: "alta" | "media" | "baixa" }) {
  const styles = {
    alta: "bg-emerald-50 text-emerald-800 border-emerald-200",
    media: "bg-amber-50 text-amber-800 border-amber-200",
    baixa: "bg-violet-50 text-violet-800 border-violet-200",
  };

  return (
    <span
      className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider border ${styles[level]}`}
    >
      IA: {level}
    </span>
  );
}

export function OriginalFragment({ text }: { text: string }) {
  const [show, setShow] = useState(false);

  return (
    <div className="mt-4 pt-3.5 border-t border-slate-200">
      <button
        onClick={() => setShow(!show)}
        className="flex items-center gap-1 text-[10px] text-slate-600 hover:text-indigo-600 font-semibold transition-colors outline-none"
      >
        {show ? (
          <>
            <EyeOff className="w-3.5 h-3.5" />
            Ocultar fragmento original do PDF
          </>
        ) : (
          <>
            <Eye className="w-3.5 h-3.5" />
            Visualizar fragmento original do PDF
          </>
        )}
      </button>
      {show && (
        <blockquote className="mt-2.5 p-3 rounded-lg bg-slate-50 border-l-4 border-indigo-300 text-[10.5px] italic text-slate-600 leading-relaxed font-mono">
          &quot;{text}&quot;
        </blockquote>
      )}
    </div>
  );
}

export function ActionPanel({
  status,
  onConfirm,
  onEdit,
  onDiscard,
}: {
  status: "pendente" | "confirmado" | "editado" | "descartado";
  onConfirm: () => void;
  onEdit: () => void;
  onDiscard: () => void;
}) {
  return (
    <div className="mt-5 pt-3.5 border-t border-slate-200 flex flex-wrap justify-between items-center gap-3">
      <div className="text-[10px] flex items-center gap-1 text-slate-600">
        <Info className="w-3.5 h-3.5" />
        Status da Validação:
        <span
          className={`font-bold capitalize ml-0.5 px-1.5 py-0.5 rounded ${
            status === "confirmado"
              ? "text-emerald-800 bg-emerald-100"
              : status === "editado"
              ? "text-indigo-800 bg-indigo-100"
              : status === "descartado"
              ? "text-rose-800 bg-rose-100"
              : "text-amber-800 bg-amber-100"
          }`}
        >
          {status}
        </span>
      </div>
      <div className="flex gap-2">
        {status !== "descartado" && (
          <button
            onClick={onDiscard}
            className="py-1 px-2.5 bg-white hover:bg-rose-50 border border-slate-300 hover:border-rose-300 text-[10px] text-slate-600 hover:text-rose-700 font-semibold rounded-lg transition-all flex items-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Descartar
          </button>
        )}
        <button
          onClick={onEdit}
          className="py-1 px-2.5 bg-white hover:bg-indigo-50 border border-slate-300 hover:border-indigo-300 text-[10px] text-slate-600 hover:text-indigo-700 font-semibold rounded-lg transition-all flex items-center gap-1.5"
        >
          <Edit2 className="w-3.5 h-3.5" />
          Corrigir
        </button>
        {status === "pendente" && (
          <button
            onClick={onConfirm}
            className="py-1 px-3 bg-emerald-600 hover:bg-emerald-500 text-[10px] font-bold text-white rounded-lg shadow-sm transition-all flex items-center gap-1.5"
          >
            <Check className="w-3.5 h-3.5" />
            Confirmar
          </button>
        )}
      </div>
    </div>
  );
}

export function EmptyState({ tab }: { tab: string }) {
  return (
    <div className="glow-card rounded-xl p-8 text-center text-slate-600 text-xs">
      <FileText className="w-10 h-10 text-slate-400 mx-auto mb-3" />
      Nenhum {tab} cadastrado ou processado ainda para este docente.
    </div>
  );
}

export function SimpleMarkdownRenderer({ content }: { content: string }) {
  if (!content) return null;

  const lines = content.split("\n");

  const parseInline = (text: string) => {
    const parts: React.ReactNode[] = [];
    let currentIdx = 0;
    const regex = /(\*\*.*?\*\*|`.*?`)/g;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(text)) !== null) {
      const matchText = match[0];
      const matchIndex = match.index;
      if (matchIndex > currentIdx) {
        parts.push(text.slice(currentIdx, matchIndex));
      }
      if (matchText.startsWith("**") && matchText.endsWith("**")) {
        parts.push(
          <strong key={matchIndex} className="text-slate-900 font-extrabold">
            {matchText.slice(2, -2)}
          </strong>
        );
      } else if (matchText.startsWith("`") && matchText.endsWith("`")) {
        parts.push(
          <code
            key={matchIndex}
            className="bg-slate-100 border border-slate-200 text-indigo-700 font-mono px-1 rounded text-[11px]"
          >
            {matchText.slice(1, -1)}
          </code>
        );
      }
      currentIdx = regex.lastIndex;
    }
    if (currentIdx < text.length) {
      parts.push(text.slice(currentIdx));
    }
    return parts.length > 0 ? parts : text;
  };

  let inList = false;
  let listItems: React.ReactNode[] = [];
  let inTable = false;
  let tableHeaders: string[] = [];
  let tableRows: string[][] = [];
  const renderedBlocks: React.ReactNode[] = [];

  const flushList = (key: string) => {
    if (inList && listItems.length > 0) {
      renderedBlocks.push(
        <ul key={`ul-${key}`} className="list-disc pl-5 my-3 space-y-1.5 text-slate-700">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  const flushTable = (key: string) => {
    if (inTable && (tableHeaders.length > 0 || tableRows.length > 0)) {
      renderedBlocks.push(
        <div key={`table-wrapper-${key}`} className="overflow-x-auto my-4 rounded-lg border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-100">
              <tr>
                {tableHeaders.map((h, i) => (
                  <th
                    key={i}
                    className="px-4 py-2 text-left font-bold text-slate-700 uppercase tracking-wider border-r border-slate-200 last:border-r-0"
                  >
                    {parseInline(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {tableRows.map((row, ri) => (
                <tr key={ri} className="hover:bg-slate-50 transition-colors">
                  {row.map((cell, ci) => (
                    <td
                      key={ci}
                      className="px-4 py-2.5 text-slate-700 border-r border-slate-100 last:border-r-0"
                    >
                      {parseInline(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableHeaders = [];
      tableRows = [];
      inTable = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (line.startsWith("|") && line.endsWith("|")) {
      flushList(String(i));
      const cells = line.split("|").slice(1, -1).map((c) => c.trim());
      const isSeparator = cells.every((c) => c.match(/^:?-+:?$/));
      if (isSeparator) {
        inTable = true;
        continue;
      }
      if (!inTable) {
        tableHeaders = cells;
        inTable = true;
      } else {
        tableRows.push(cells);
      }
      continue;
    }
    flushTable(String(i));

    if (line.startsWith("* ") || line.startsWith("- ")) {
      inList = true;
      const text = line.substring(2);
      listItems.push(
        <li key={`li-${i}-${text.slice(0, 10)}`} className="leading-relaxed">
          {parseInline(text)}
        </li>
      );
      continue;
    }
    flushList(String(i));

    if (line.startsWith("# ")) {
      renderedBlocks.push(
        <h1
          key={`h1-${i}`}
          className="text-lg font-extrabold text-slate-900 mt-5 mb-3 pb-1.5 border-b border-slate-200 uppercase tracking-wide"
        >
          {parseInline(line.substring(2))}
        </h1>
      );
    } else if (line.startsWith("## ")) {
      renderedBlocks.push(
        <h2
          key={`h2-${i}`}
          className="text-sm font-extrabold text-indigo-700 mt-4 mb-2 uppercase tracking-wider flex items-center gap-2"
        >
          {parseInline(line.substring(3))}
        </h2>
      );
    } else if (line.startsWith("### ")) {
      renderedBlocks.push(
        <h3
          key={`h3-${i}`}
          className="text-xs font-bold text-slate-700 mt-3 mb-1.5 uppercase tracking-widest"
        >
          {parseInline(line.substring(4))}
        </h3>
      );
    } else if (line.startsWith("> ")) {
      renderedBlocks.push(
        <blockquote
          key={`bq-${i}`}
          className="my-3 p-3 bg-indigo-50 border-l-4 border-indigo-400 rounded-r-lg text-slate-600 italic text-[11px] leading-relaxed"
        >
          {parseInline(line.substring(2))}
        </blockquote>
      );
    } else if (line === "---") {
      renderedBlocks.push(<hr key={`hr-${i}`} className="my-4 border-slate-200" />);
    } else if (line.length > 0) {
      renderedBlocks.push(
        <p key={`p-${i}`} className="my-2.5 text-slate-700 leading-relaxed">
          {parseInline(line)}
        </p>
      );
    }
  }

  flushList("end");
  flushTable("end");
  return <div className="space-y-1">{renderedBlocks}</div>;
}
