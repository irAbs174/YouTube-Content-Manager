"use client";

import type { ContentRow } from "@/lib/types";
import { shorten } from "@/lib/format";

interface RenderCellProps {
  row: ContentRow;
  onRender: (row: ContentRow) => void;
  onPreview: (row: ContentRow) => void;
}

const smallBtn =
  "rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800";

export function RenderCell({ row, onRender, onPreview }: RenderCellProps) {
  switch (row.renderStatus) {
    case "queued":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400" aria-hidden />
          Queued
        </span>
      );

    case "running": {
      const pct = Math.max(0, Math.min(100, Math.round(row.renderProgress)));
      return (
        <div className="flex min-w-28 items-center gap-2" aria-label={`Rendering ${pct}%`}>
          <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
            <div
              className="h-full rounded-full bg-linear-to-r from-cyan-400 to-indigo-500 transition-[width] duration-500 ease-out"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="w-9 text-xs font-semibold tabular-nums text-slate-600 dark:text-slate-300">{pct}%</span>
        </div>
      );
    }

    case "done":
      return (
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => onPreview(row)}
            className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-2.5 py-1 text-xs font-semibold text-white shadow-sm shadow-emerald-600/30 transition hover:bg-emerald-500"
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
              <path d="M8 5v14l11-7z" />
            </svg>
            Play
          </button>
          <button type="button" onClick={() => onRender(row)} className={smallBtn} title="Re-render with FFmpeg">
            ↻
          </button>
        </div>
      );

    case "failed":
      return (
        <div className="flex items-center gap-1.5">
          <span
            className="rounded-full bg-rose-100 px-2.5 py-1 text-xs font-semibold text-rose-700 dark:bg-rose-500/15 dark:text-rose-300"
            title={row.renderError ?? "Render failed"}
          >
            Failed
          </span>
          <button type="button" onClick={() => onRender(row)} className={smallBtn}>
            Retry
          </button>
          {row.renderError && (
            <span className="hidden max-w-40 truncate text-[11px] text-slate-400 xl:inline" title={row.renderError}>
              {shorten(row.renderError, 40)}
            </span>
          )}
        </div>
      );

    default:
      return (
        <button type="button" onClick={() => onRender(row)} className={smallBtn}>
          Render
        </button>
      );
  }
}
