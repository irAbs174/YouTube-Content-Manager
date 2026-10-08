"use client";

import { useId, useMemo } from "react";
import { fmtCompact, fmtHours, fmtInt, fmtPct } from "@/lib/format";
import type { DashboardData, KpiKey, KpiPair, SeriesPoint } from "@/lib/types";
import { useTween } from "./hooks";

interface KpiDef {
  key: KpiKey;
  label: string;
  color: string;
  format: (n: number) => string;
  pick: (p: SeriesPoint) => number;
}

const KPI_DEFS: KpiDef[] = [
  { key: "views", label: "Total views", color: "#6366f1", format: fmtCompact, pick: (p) => p.views },
  { key: "watchHours", label: "Watch time", color: "#06b6d4", format: fmtHours, pick: (p) => p.watchHours },
  { key: "subs", label: "Subscribers", color: "#10b981", format: fmtInt, pick: (p) => p.subs },
  { key: "ctr", label: "Avg CTR", color: "#f59e0b", format: (n) => fmtPct(n), pick: (p) => p.ctr },
  { key: "likes", label: "Likes", color: "#f43f5e", format: fmtCompact, pick: (p) => p.likes },
];

export function KpiCards({ data }: { data: DashboardData }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-5">
      {KPI_DEFS.map((def) => (
        <KpiCard
          key={def.key}
          def={def}
          pair={data.kpis[def.key]}
          series={data.series}
          days={data.range.days}
        />
      ))}
    </div>
  );
}

function KpiCard({
  def,
  pair,
  series,
  days,
}: {
  def: KpiDef;
  pair: KpiPair;
  series: SeriesPoint[];
  days: number;
}) {
  const animated = useTween(pair.value);
  const delta = pair.prev > 0 ? ((pair.value - pair.prev) / pair.prev) * 100 : null;
  const values = useMemo(() => series.map(def.pick), [series, def]);

  return (
    <article className="dashboard-fade-in group relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-slate-900/5 sm:p-5 dark:border-slate-800 dark:bg-slate-900/70 dark:hover:shadow-black/30">
      <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
        <span className="h-2 w-2 rounded-full" style={{ background: def.color }} aria-hidden />
        <span className="truncate">{def.label}</span>
      </div>

      <p className="mt-2 text-2xl font-semibold tabular-nums tracking-tight sm:text-3xl">
        {def.format(animated)}
      </p>

      <div className="mt-3 flex items-end justify-between gap-2">
        <div className="min-w-0 space-y-1">
          <TrendPill delta={delta} />
          <p className="truncate text-[11px] text-slate-500 dark:text-slate-400">vs prior {days}d</p>
        </div>
        <Sparkline values={values} color={def.color} />
      </div>
    </article>
  );
}

function TrendPill({ delta }: { delta: number | null }) {
  if (delta === null) {
    return <span className="text-xs text-slate-400">No prior data</span>;
  }
  const up = delta >= 0;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums transition-colors ${
        up
          ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300"
          : "bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300"
      }`}
    >
      <svg width="9" height="9" viewBox="0 0 10 10" className={`transition-transform duration-300 ${up ? "" : "rotate-180"}`} aria-hidden>
        <path d="M5 1 L9 8 L1 8 Z" fill="currentColor" />
      </svg>
      {Math.abs(delta).toFixed(1)}%
    </span>
  );
}

function Sparkline({ values, color }: { values: number[]; color: string }) {
  const reactId = useId();
  const gradientId = `spark-${reactId.replace(/:/g, "")}`;

  const path = useMemo(() => {
    if (values.length === 0) return "";
    const max = Math.max(...values, 1);
    const min = Math.min(...values, 0);
    const span = max - min || 1;
    const step = 120 / Math.max(values.length - 1, 1);
    return values
      .map((v, i) => `${i === 0 ? "M" : "L"}${(i * step).toFixed(1)},${(38 - ((v - min) / span) * 34).toFixed(1)}`)
      .join(" ");
  }, [values]);

  return (
    <svg viewBox="0 0 120 40" preserveAspectRatio="none" className="h-10 w-20 shrink-0 sm:w-28" aria-hidden>
      <defs>
        <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.35} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <path d={path ? `${path} L120,40 L0,40 Z` : ""} fill={`url(#${gradientId})`} style={{ transition: "d 0.6s ease" }} />
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
        style={{ transition: "d 0.6s ease" }}
      />
    </svg>
  );
}
