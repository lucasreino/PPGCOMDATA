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
    alta: "bg-emerald-950/60 text-emerald-400 border-emerald-900/60",
    media: "bg-amber-950/60 text-amber-400 border-amber-900/60",
    baixa: "bg-purple-950/60 text-purple-400 border-purple-900/60",
  };

  return (
    <span
      className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider border shadow-sm ${styles[level]}`}
    >
      IA: {level}
    </span>
  );
}

export function OriginalFragment({ text }: { text: string }) {
  const [show, setShow] = useState(false);

  return (
    <div className="mt-4 pt-3.5 border-t border-slate-900/80">
      <button
        onClick={() => setShow(!show)}
        className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-indigo-400 font-semibold transition-colors outline-none"
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
        <blockquote className="mt-2.5 p-3 rounded bg-slate-950 border-l-2 border-slate-800 text-[10.5px] italic text-slate-500 leading-relaxed font-mono">
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
    <div className="mt-5 pt-3.5 border-t border-slate-900/80 flex flex-wrap justify-between items-center gap-3">
      <div className="text-[10px] flex items-center gap-1 text-slate-500">
        <Info className="w-3.5 h-3.5" />
        Status da Validação:
        <span
          className={`font-bold capitalize ml-0.5 px-1 rounded ${
            status === "confirmado"
              ? "text-emerald-400 bg-emerald-950/30"
              : status === "editado"
              ? "text-indigo-400 bg-indigo-950/30"
              : status === "descartado"
              ? "text-rose-400 bg-rose-950/30"
              : "text-amber-400 bg-amber-950/30"
          }`}
        >
          {status}
        </span>
      </div>
      <div className="flex gap-2">
        {status !== "descartado" && (
          <button
            onClick={onDiscard}
            className="py-1 px-2.5 bg-slate-900/60 hover:bg-rose-950/20 border border-slate-800 hover:border-rose-900/60 text-[10px] text-slate-400 hover:text-rose-400 font-semibold rounded-lg transition-all flex items-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Descartar
          </button>
        )}
        <button
          onClick={onEdit}
          className="py-1 px-2.5 bg-slate-900/60 hover:bg-indigo-950/40 border border-slate-800 hover:border-indigo-900/60 text-[10px] text-slate-400 hover:text-indigo-400 font-semibold rounded-lg transition-all flex items-center gap-1.5"
        >
          <Edit2 className="w-3.5 h-3.5" />
          Corrigir
        </button>
        {status === "pendente" && (
          <button
            onClick={onConfirm}
            className="py-1 px-3 bg-emerald-600 hover:bg-emerald-500 text-[10px] font-bold text-white rounded-lg shadow-md shadow-emerald-950/20 transition-all flex items-center gap-1.5"
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
    <div className="glow-card rounded-xl p-8 text-center text-slate-500 text-xs">
      <FileText className="w-10 h-10 text-slate-600/80 mx-auto mb-3" />
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
          <strong key={matchIndex} className="text-white font-extrabold">
            {matchText.slice(2, -2)}
          </strong>
        );
      } else if (matchText.startsWith("`") && matchText.endsWith("`")) {
        parts.push(
          <code
            key={matchIndex}
            className="bg-slate-900 border border-slate-800 text-indigo-300 font-mono px-1 rounded text-[11px]"
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
        <ul key={`ul-${key}`} className="list-disc pl-5 my-3 space-y-1.5 text-slate-350">
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
        <div key={`table-wrapper-${key}`} className="overflow-x-auto my-4 rounded-lg border border-slate-850">
          <table className="min-w-full divide-y divide-slate-850 text-xs">
            <thead className="bg-slate-900/60">
              <tr>
                {tableHeaders.map((h, i) => (
                  <th
                    key={i}
                    className="px-4 py-2 text-left font-bold text-slate-300 uppercase tracking-wider border-r border-slate-850 last:border-r-0"
                  >
                    {parseInline(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-900 bg-slate-950/20">
              {tableRows.map((row, ri) => (
                <tr key={ri} className="hover:bg-slate-900/20 transition-colors">
                  {row.map((cell, ci) => (
                    <td
                      key={ci}
                      className="px-4 py-2.5 text-slate-300 border-r border-slate-900 last:border-r-0"
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
          className="text-lg font-extrabold text-white mt-5 mb-3 pb-1.5 border-b border-slate-900 uppercase tracking-wide"
        >
          {parseInline(line.substring(2))}
        </h1>
      );
    } else if (line.startsWith("## ")) {
      renderedBlocks.push(
        <h2
          key={`h2-${i}`}
          className="text-sm font-extrabold text-indigo-400 mt-4 mb-2 uppercase tracking-wider flex items-center gap-2"
        >
          {parseInline(line.substring(3))}
        </h2>
      );
    } else if (line.startsWith("### ")) {
      renderedBlocks.push(
        <h3
          key={`h3-${i}`}
          className="text-xs font-bold text-slate-300 mt-3 mb-1.5 uppercase tracking-widest"
        >
          {parseInline(line.substring(4))}
        </h3>
      );
    } else if (line.startsWith("> ")) {
      renderedBlocks.push(
        <blockquote
          key={`bq-${i}`}
          className="my-3 p-3 bg-slate-900/40 border-l-2 border-indigo-600 rounded-r-lg text-slate-400 italic text-[11px] leading-relaxed"
        >
          {parseInline(line.substring(2))}
        </blockquote>
      );
    } else if (line === "---") {
      renderedBlocks.push(<hr key={`hr-${i}`} className="my-4 border-slate-900" />);
    } else if (line.length > 0) {
      renderedBlocks.push(
        <p key={`p-${i}`} className="my-2.5 text-slate-350 leading-relaxed">
          {parseInline(line)}
        </p>
      );
    }
  }

  flushList("end");
  flushTable("end");
  return <div className="space-y-1">{renderedBlocks}</div>;
}
