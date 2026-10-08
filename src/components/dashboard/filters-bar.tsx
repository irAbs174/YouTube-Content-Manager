"use client";

import { COLLECTIONS, STATUSES, type Preset } from "@/lib/constants";
import { inputClass } from "./ui";

const PRESETS: Preset[] = ["7D", "30D", "90D", "180D", "Custom"];

interface FiltersBarProps {
  preset: Preset;
  from: string;
  to: string;
  days: number;
  collection: string;
  status: string;
  onPreset: (p: Preset) => void;
  onFrom: (v: string) => void;
  onTo: (v: string) => void;
  onCollection: (v: string) => void;
  onStatus: (v: string) => void;
  onReset: () => void;
}

export function FiltersBar(props: FiltersBarProps) {
  const { preset, from, to, days, collection, status } = props;
  const dirty = collection !== "All" || status !== "All";

  return (
    <section
      aria-label="Filters"
      className="dashboard-fade-in space-y-4 rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-sm backdrop-blur transition-colors sm:p-5 dark:border-slate-800 dark:bg-slate-900/70"
    >
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        {/* Date range */}
        <div className="flex flex-wrap items-center gap-3">
          <div
            role="group"
            aria-label="Date range preset"
            className="inline-flex rounded-xl bg-slate-100 p-1 dark:bg-slate-800"
          >
            {PRESETS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => props.onPreset(p)}
                aria-pressed={preset === p}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all sm:text-sm ${
                  preset === p
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white"
                    : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
                }`}
              >
                {p === "Custom" ? "Custom" : p}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <label className="sr-only" htmlFor="from-date">From</label>
            <input
              id="from-date"
              type="date"
              value={from}
              max={to}
              onChange={(e) => e.target.value && props.onFrom(e.target.value)}
              className={`${inputClass} w-auto py-1.5 text-xs sm:text-sm`}
            />
            <span className="text-xs text-slate-400">→</span>
            <label className="sr-only" htmlFor="to-date">To</label>
            <input
              id="to-date"
              type="date"
              value={to}
              min={from}
              onChange={(e) => e.target.value && props.onTo(e.target.value)}
              className={`${inputClass} w-auto py-1.5 text-xs sm:text-sm`}
            />
          </div>

          <span className="hidden rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-700 sm:inline-flex dark:bg-indigo-500/15 dark:text-indigo-300">
            {days} days
          </span>
        </div>

        {/* Status + reset */}
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor="status-filter" className="text-xs font-medium text-slate-500 dark:text-slate-400">
            Status
          </label>
          <select
            id="status-filter"
            value={status}
            onChange={(e) => props.onStatus(e.target.value)}
            className={`${inputClass} w-auto py-1.5 pr-8 text-xs sm:text-sm`}
          >
            <option value="All">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          {dirty && (
            <button
              type="button"
              onClick={props.onReset}
              className="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-rose-600 transition hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-500/10"
            >
              Reset filters
            </button>
          )}
        </div>
      </div>

      {/* Segment (collection) chips */}
      <div>
        <p className="mb-2 text-xs font-medium text-slate-500 dark:text-slate-400">Segment</p>
        <div className="thin-scroll flex gap-2 overflow-x-auto pb-1">
          {["All", ...COLLECTIONS.map((c) => c.name)].map((name) => {
            const active = collection === name;
            const color = COLLECTIONS.find((c) => c.name === name)?.color;
            return (
              <button
                key={name}
                type="button"
                onClick={() => props.onCollection(name)}
                aria-pressed={active}
                className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-all duration-200 sm:text-sm ${
                  active
                    ? "border-slate-900 bg-slate-900 text-white shadow-md dark:border-white dark:bg-white dark:text-slate-900"
                    : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-slate-500 dark:hover:text-white"
                }`}
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: color ?? "linear-gradient(90deg,#22d3ee,#6366f1,#f43f5e)" }}
                  aria-hidden
                />
                {name}
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
