"use client";

import { ImageDown } from "lucide-react";
import { downloadChartPng, type ChartExportSpec } from "@/lib/chartExport";

export function ChartPanel({
  title,
  exportSpec,
  children,
}: {
  title: string;
  exportSpec?: ChartExportSpec;
  children: React.ReactNode;
}) {
  return (
    <div className="glow-card rounded-xl p-5">
      <div className="flex items-center justify-between gap-2 mb-3">
        <h3 className="text-sm font-semibold text-slate-300">{title}</h3>
        {exportSpec && (
          <button
            type="button"
            title="Exportar PNG"
            onClick={() =>
              downloadChartPng(exportSpec, `${exportSpec.title.replace(/\s+/g, "_")}.png`)
            }
            className="flex items-center gap-1 text-[10px] px-2 py-1 border border-slate-700 rounded hover:border-indigo-600 text-slate-400"
          >
            <ImageDown className="w-3 h-3" /> PNG
          </button>
        )}
      </div>
      {children}
    </div>
  );
}

interface BarChartProps {
  data: Record<string, number>;
  maxBars?: number;
  color?: string;
  valueFormat?: (n: number) => string;
}

export function SimpleBarChart({
  data,
  maxBars = 12,
  color = "#6366f1",
  valueFormat = (n) => String(n),
}: BarChartProps) {
  const entries = Object.entries(data)
    .sort((a, b) => b[1] - a[1])
    .slice(0, maxBars);
  if (entries.length === 0) {
    return <p className="text-xs text-slate-500 py-8 text-center">Sem dados para exibir</p>;
  }
  const max = Math.max(...entries.map(([, v]) => v), 1);

  return (
    <div className="space-y-2.5 pt-1">
      {entries.map(([label, value]) => (
        <div key={label} className="space-y-1">
          <div className="flex justify-between text-[10px] text-slate-400">
            <span className="truncate max-w-[70%]" title={label}>
              {label}
            </span>
            <span className="font-mono text-slate-300">{valueFormat(value)}</span>
          </div>
          <div className="h-2 bg-slate-900 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${(value / max) * 100}%`, backgroundColor: color }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

interface LineChartProps {
  data: Record<string, number>;
  color?: string;
}

export function SimpleLineChart({ data, color = "#6366f1" }: LineChartProps) {
  const years = Object.keys(data).sort();
  if (years.length === 0) {
    return <p className="text-xs text-slate-500 py-8 text-center">Sem dados históricos</p>;
  }
  const values = years.map((y) => data[y]);
  const maxVal = Math.max(...values, 1);
  const points = years.map((yr, idx) => {
    const x = years.length === 1 ? 250 : (idx / (years.length - 1)) * 480 + 10;
    const y = 170 - (values[idx] / maxVal) * 140;
    return { x, y, year: yr, value: values[idx] };
  });
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  const areaPath = `${linePath} L ${points[points.length - 1].x} 180 L ${points[0].x} 180 Z`;

  return (
    <div>
      <svg className="w-full h-44" viewBox="0 0 500 200" preserveAspectRatio="none">
        <defs>
          <linearGradient id="dossieLineGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.35" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <line x1="0" y1="50" x2="500" y2="50" stroke="#1e293b" strokeDasharray="3 3" strokeWidth="0.5" />
        <line x1="0" y1="100" x2="500" y2="100" stroke="#1e293b" strokeDasharray="3 3" strokeWidth="0.5" />
        <line x1="0" y1="150" x2="500" y2="150" stroke="#1e293b" strokeDasharray="3 3" strokeWidth="0.5" />
        <path d={areaPath} fill="url(#dossieLineGrad)" />
        <path d={linePath} fill="none" stroke={color} strokeWidth="2.5" />
        {points.map((p) => (
          <circle key={p.year} cx={p.x} cy={p.y} r="4" fill={color} stroke="#0f172a" strokeWidth="2" />
        ))}
      </svg>
      <div className="flex justify-between text-[9px] text-slate-500 px-1">
        {years.map((y) => (
          <span key={y}>{y}</span>
        ))}
      </div>
    </div>
  );
}

interface StackedBarProps {
  data: Record<string, Record<string, number>>;
  keys?: string[];
  colors?: string[];
}

export function StackedBarChart({
  data,
  keys = ["pesquisa", "extensao", "artigos", "livros"],
  colors = ["#6366f1", "#10b981", "#a855f7", "#f59e0b"],
}: StackedBarProps) {
  const entries = Object.entries(data);
  if (entries.length === 0) {
    return <p className="text-xs text-slate-500 py-8 text-center">Sem dados</p>;
  }
  const maxTotal = Math.max(
    ...entries.map(([, v]) => Object.values(v).reduce((a, b) => a + b, 0)),
    1
  );

  return (
    <div className="space-y-3">
      {entries.map(([label, parts]) => {
        const total = Object.values(parts).reduce((a, b) => a + b, 0);
        return (
          <div key={label}>
            <div className="flex justify-between text-[10px] text-slate-400 mb-1">
              <span className="truncate max-w-[65%]">{label}</span>
              <span>{total}</span>
            </div>
            <div className="h-3 flex rounded-full overflow-hidden bg-slate-900">
              {keys.map((k, i) => {
                const val = parts[k] || 0;
                if (!val) return null;
                const w = (val / maxTotal) * 100;
                return (
                  <div
                    key={k}
                    style={{ width: `${w}%`, backgroundColor: colors[i % colors.length] }}
                    title={`${k}: ${val}`}
                  />
                );
              })}
            </div>
          </div>
        );
      })}
      <div className="flex flex-wrap gap-3 text-[9px] text-slate-500 pt-2">
        {keys.map((k, i) => (
          <span key={k} className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-sm inline-block"
              style={{ backgroundColor: colors[i % colors.length] }}
            />
            {k}
          </span>
        ))}
      </div>
    </div>
  );
}

export function KpiCard({
  label,
  value,
  sub,
  accent = "indigo",
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "indigo" | "emerald" | "purple" | "amber" | "rose";
}) {
  const colors: Record<string, string> = {
    indigo: "from-indigo-950/30 text-indigo-400 border-indigo-800/40",
    emerald: "from-emerald-950/30 text-emerald-400 border-emerald-800/40",
    purple: "from-purple-950/30 text-purple-400 border-purple-800/40",
    amber: "from-amber-950/30 text-amber-400 border-amber-800/40",
    rose: "from-rose-950/30 text-rose-400 border-rose-800/40",
  };
  return (
    <div className={`glow-card rounded-xl p-5 border bg-gradient-to-br to-slate-900/30 ${colors[accent]}`}>
      <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">{label}</span>
      <h3 className={`text-2xl font-bold mt-1 ${colors[accent].split(" ")[1]}`}>{value}</h3>
      {sub && <p className="text-[9px] text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}
