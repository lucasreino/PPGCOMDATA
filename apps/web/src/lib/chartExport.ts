/** Gera PNG a partir de dados de gráfico (sem dependências externas). */

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function setupCanvas(title: string, width = 720, height = 420) {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas não suportado");
  ctx.fillStyle = "#0f172a";
  ctx.fillRect(0, 0, width, height);
  ctx.fillStyle = "#e2e8f0";
  ctx.font = "bold 16px system-ui, sans-serif";
  ctx.fillText(title, 24, 32);
  return { canvas, ctx, width, height };
}

export function downloadBarChartPng(
  title: string,
  data: Record<string, number>,
  color = "#6366f1",
  filename?: string
) {
  const entries = Object.entries(data)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 14);
  if (entries.length === 0) return;

  const { canvas, ctx, width, height } = setupCanvas(title);
  const max = Math.max(...entries.map(([, v]) => v), 1);
  const barH = 22;
  const gap = 10;
  let y = 56;

  entries.forEach(([label, value]) => {
    ctx.fillStyle = "#94a3b8";
    ctx.font = "12px system-ui, sans-serif";
    const short = label.length > 42 ? `${label.slice(0, 40)}…` : label;
    ctx.fillText(short, 24, y + 14);
    ctx.fillStyle = "#cbd5e1";
    ctx.fillText(String(value), width - 80, y + 14);
    ctx.fillStyle = "#1e293b";
    ctx.fillRect(24, y + 18, width - 48, barH);
    const w = ((width - 48) * value) / max;
    ctx.fillStyle = color;
    ctx.fillRect(24, y + 18, w, barH);
    y += barH + gap + 18;
  });

  canvas.toBlob((blob) => {
    if (blob) triggerDownload(blob, filename || `${title.replace(/\s+/g, "_")}.png`);
  }, "image/png");
}

export function downloadLineChartPng(
  title: string,
  data: Record<string, number>,
  color = "#6366f1",
  filename?: string
) {
  const years = Object.keys(data).sort();
  if (years.length === 0) return;

  const values = years.map((y) => data[y]);
  const maxVal = Math.max(...values, 1);
  const { canvas, ctx, width, height } = setupCanvas(title, 720, 400);
  const padL = 48;
  const padR = 24;
  const padT = 56;
  const padB = 48;
  const chartW = width - padL - padR;
  const chartH = height - padT - padB;

  ctx.strokeStyle = "#334155";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const gy = padT + (chartH * i) / 4;
    ctx.beginPath();
    ctx.moveTo(padL, gy);
    ctx.lineTo(width - padR, gy);
    ctx.stroke();
  }

  const points = years.map((yr, idx) => {
    const x =
      years.length === 1
        ? padL + chartW / 2
        : padL + (idx / (years.length - 1)) * chartW;
    const y = padT + chartH - (values[idx] / maxVal) * chartH;
    return { x, y, yr, value: values[idx] };
  });

  ctx.beginPath();
  ctx.moveTo(points[0].x, padT + chartH);
  points.forEach((p) => ctx.lineTo(p.x, p.y));
  ctx.lineTo(points[points.length - 1].x, padT + chartH);
  ctx.closePath();
  const grad = ctx.createLinearGradient(0, padT, 0, padT + chartH);
  grad.addColorStop(0, color + "55");
  grad.addColorStop(1, color + "00");
  ctx.fillStyle = grad;
  ctx.fill();

  ctx.strokeStyle = color;
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  points.forEach((p, i) => {
    if (i === 0) ctx.moveTo(p.x, p.y);
    else ctx.lineTo(p.x, p.y);
  });
  ctx.stroke();

  points.forEach((p) => {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#64748b";
    ctx.font = "10px system-ui, sans-serif";
    ctx.fillText(p.yr, p.x - 12, height - 20);
  });

  canvas.toBlob((blob) => {
    if (blob) triggerDownload(blob, filename || `${title.replace(/\s+/g, "_")}.png`);
  }, "image/png");
}

export type ChartExportSpec =
  | { kind: "bar"; title: string; data: Record<string, number>; color?: string }
  | { kind: "line"; title: string; data: Record<string, number>; color?: string };

export function downloadChartPng(spec: ChartExportSpec, filename?: string) {
  if (spec.kind === "line") {
    downloadLineChartPng(spec.title, spec.data, spec.color, filename);
  } else {
    downloadBarChartPng(spec.title, spec.data, spec.color, filename);
  }
}
