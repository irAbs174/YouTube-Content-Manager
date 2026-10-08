"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fmtCompact, fmtInt } from "@/lib/format";
import { EmptyState } from "./ui";

// ── shared styling ───────────────────────────────────────────────────────────
// Axis / grid colours follow `currentColor`, so the parent sets light/dark text colour.
const AXIS_TICK = { fill: "currentColor", fontSize: 11 };
const AXIS_LINE = { stroke: "currentColor", strokeOpacity: 0.15 };
const GRID_PROPS = { stroke: "currentColor", strokeOpacity: 0.12, strokeDasharray: "3 3" } as const;

type TooltipItem = {
  name?: string | number;
  value?: number | string;
  color?: string;
  dataKey?: string | number;
  payload?: unknown;
};

export function ChartTooltip({
  active,
  payload,
  label,
  format = (v: number) => fmtInt(v),
}: {
  active?: boolean;
  payload?: readonly TooltipItem[];
  label?: string | number;
  format?: (value: number, key: string) => string;
}) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="pointer-events-none min-w-36 rounded-xl border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-xl shadow-slate-900/10 backdrop-blur dark:border-slate-700 dark:bg-slate-900/95 dark:shadow-black/40">
      {label !== undefined && (
        <p className="mb-1.5 font-semibold text-slate-700 dark:text-slate-200">{String(label)}</p>
      )}
      <div className="space-y-1">
        {payload.map((item, i) => {
          const color =
            item.color ?? (item.payload as { color?: string; fill?: string } | undefined)?.color ??
            (item.payload as { fill?: string } | undefined)?.fill ?? "#94a3b8";
          const value = Number(item.value ?? 0);
          return (
            <div key={`${String(item.name)}-${i}`} className="flex items-center gap-2">
              <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: color }} />
              <span className="text-slate-500 dark:text-slate-400">{String(item.name ?? "")}</span>
              <span className="ml-auto pl-4 font-semibold tabular-nums text-slate-900 dark:text-white">
                {format(value, String(item.dataKey ?? ""))}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── line chart: trend ────────────────────────────────────────────────────────
export interface TrendPoint {
  label: string;
  day: string;
  views: number;
  subs: number;
}

export function TrendChart({ points }: { points: TrendPoint[] }) {
  if (points.length === 0) return <EmptyState text="No activity in this range" />;
  return (
    <div className="h-72 w-full text-slate-500 dark:text-slate-400">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 36, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid vertical={false} {...GRID_PROPS} />
          <XAxis dataKey="label" tick={AXIS_TICK} tickLine={false} axisLine={AXIS_LINE} minTickGap={28} />
          <YAxis
            yAxisId="views"
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            width={48}
            tickFormatter={(v: number) => fmtCompact(v)}
          />
          <YAxis
            yAxisId="subs"
            orientation="right"
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            width={44}
            tickFormatter={(v: number) => fmtCompact(v)}
          />
          <Tooltip
            content={<ChartTooltip format={(v, key) => (key === "subs" ? fmtInt(v) : fmtCompact(v))} />}
            cursor={{ stroke: "currentColor", strokeOpacity: 0.25, strokeDasharray: "4 4" }}
          />
          <Legend verticalAlign="top" align="left" iconType="circle" height={32} wrapperStyle={{ fontSize: 12 }} />
          <Line
            yAxisId="views"
            name="Views"
            dataKey="views"
            type="monotone"
            stroke="#6366f1"
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 5, strokeWidth: 2, stroke: "#fff" }}
            isAnimationActive
            animationDuration={800}
            animationEasing="ease-in-out"
          />
          <Line
            yAxisId="subs"
            name="Subscribers"
            dataKey="subs"
            type="monotone"
            stroke="#10b981"
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 5, strokeWidth: 2, stroke: "#fff" }}
            isAnimationActive
            animationDuration={800}
            animationEasing="ease-in-out"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── donut: status mix ────────────────────────────────────────────────────────
export interface MixSlice {
  name: string;
  value: number;
  color: string;
}

export function StatusDonut({ data, total }: { data: MixSlice[]; total: number }) {
  if (data.length === 0) return <EmptyState text="No episodes in this view" />;
  return (
    <div className="flex h-full flex-col">
      <div className="relative mx-auto h-56 w-full max-w-60">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius="66%"
              outerRadius="94%"
              paddingAngle={3}
              stroke="none"
              cornerRadius={6}
              isAnimationActive
              animationDuration={700}
            >
              {data.map((slice) => (
                <Cell key={slice.name} fill={slice.color} />
              ))}
            </Pie>
            <Tooltip content={<ChartTooltip format={(v) => `${fmtInt(v)} ep`} />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-semibold tabular-nums tracking-tight">{fmtInt(total)}</span>
          <span className="text-[11px] uppercase tracking-wider text-slate-500 dark:text-slate-400">episodes</span>
        </div>
      </div>

      <ul className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        {data.map((slice) => {
          const pct = total > 0 ? (slice.value / total) * 100 : 0;
          return (
            <li key={slice.name} className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: slice.color }} />
              <span className="truncate text-slate-600 dark:text-slate-300">{slice.name}</span>
              <span className="ml-auto font-semibold tabular-nums">{pct.toFixed(0)}%</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// ── horizontal bar: views by collection ──────────────────────────────────────
export interface BarDatum {
  name: string;
  value: number;
  color: string;
  meta?: string;
}

export function CollectionBars({ data }: { data: BarDatum[] }) {
  if (data.length === 0) return <EmptyState text="No collections in this view" />;
  return (
    <div className="h-72 w-full text-slate-500 dark:text-slate-400">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 0 }}>
          <CartesianGrid horizontal={false} {...GRID_PROPS} />
          <XAxis type="number" tick={AXIS_TICK} tickLine={false} axisLine={false} tickFormatter={(v: number) => fmtCompact(v)} />
          <YAxis type="category" dataKey="name" width={124} tick={AXIS_TICK} tickLine={false} axisLine={false} />
          <Tooltip
            content={<ChartTooltip format={(v) => `${fmtCompact(v)} views`} />}
            cursor={{ fill: "currentColor", fillOpacity: 0.06 }}
          />
          <Bar dataKey="value" name="Views" radius={[0, 8, 8, 0]} barSize={18} isAnimationActive animationDuration={700}>
            {data.map((d) => (
              <Cell key={d.name} fill={d.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── horizontal bar: top episodes ─────────────────────────────────────────────
export function TopEpisodesBars({ data }: { data: BarDatum[] }) {
  if (data.length === 0) return <EmptyState text="No episodes with views yet" />;
  return (
    <div className="h-72 w-full text-slate-500 dark:text-slate-400">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 0 }}>
          <CartesianGrid horizontal={false} {...GRID_PROPS} />
          <XAxis type="number" tick={AXIS_TICK} tickLine={false} axisLine={false} tickFormatter={(v: number) => fmtCompact(v)} />
          <YAxis type="category" dataKey="name" width={150} tick={AXIS_TICK} tickLine={false} axisLine={false} />
          <Tooltip
            content={<ChartTooltip format={(v) => `${fmtCompact(v)} views`} />}
            cursor={{ fill: "currentColor", fillOpacity: 0.06 }}
          />
          <Bar dataKey="value" name="Views" radius={[0, 8, 8, 0]} barSize={14} isAnimationActive animationDuration={700}>
            {data.map((d) => (
              <Cell key={d.name} fill={d.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
