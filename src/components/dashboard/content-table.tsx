"use client";

import { useMemo, useState } from "react";
import { STATUS_COLORS, STATUSES, collectionColor } from "@/lib/constants";
import { formatDateLong } from "@/lib/dates";
import { fmtCompact, fmtDuration, fmtInt, fmtPct, pad2 } from "@/lib/format";
import type { ContentRow } from "@/lib/types";
import { ghostButtonClass, inputClass } from "./ui";
import { RenderCell } from "./render-cell";

type SortKey =
  | "episode"
  | "date"
  | "title"
  | "status"
  | "collection"
  | "soundMusic"
  | "effects"
  | "subtitles"
  | "thumbnail"
  | "renderStatus"
  | "views"
  | "ctr"
  | "likes"
  | "subs";

const COLUMNS: { key: SortKey; label: string; numeric?: boolean }[] = [
  { key: "episode", label: "Episode", numeric: true },
  { key: "date", label: "Date" },
  { key: "title", label: "Title" },
  { key: "status", label: "Status" },
  { key: "collection", label: "Collection" },
  { key: "soundMusic", label: "Sound / Music" },
  { key: "effects", label: "Effects" },
  { key: "subtitles", label: "Subtitles" },
  { key: "thumbnail", label: "Thumbnail" },
  { key: "renderStatus", label: "Render" },
  { key: "views", label: "Views", numeric: true },
  { key: "ctr", label: "CTR", numeric: true },
  { key: "likes", label: "Likes", numeric: true },
  { key: "subs", label: "Subs", numeric: true },
];

const PAGE_SIZE = 10;

function sortValue(row: ContentRow, key: SortKey): string | number {
  switch (key) {
    case "ctr":
      return row.impressions > 0 ? row.views / row.impressions : 0;
    case "views":
      return row.views;
    case "likes":
      return row.likes;
    case "subs":
      return row.subs;
    case "episode":
      return row.episode;
    default:
      return String(row[key] ?? "").toLowerCase();
  }
}

function csvCell(value: string | number): string {
  return `"${String(value).replace(/"/g, '""')}"`;
}

interface ContentTableProps {
  rows: ContentRow[];
  loading: boolean;
  onStatusChange: (id: number, status: string) => void;
  onDelete: (row: ContentRow) => void;
  onAdd: () => void;
  onRender: (row: ContentRow) => void;
  onPreview: (row: ContentRow) => void;
}

export function ContentTable({ rows, loading, onStatusChange, onDelete, onAdd, onRender, onPreview }: ContentTableProps) {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<{ key: SortKey; dir: "asc" | "desc" }>({ key: "episode", dir: "desc" });
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const list = q
      ? rows.filter((r) =>
          [r.episode, r.title, r.collection, r.status, r.soundMusic, r.effects, r.subtitles]
            .join(" ")
            .toLowerCase()
            .includes(q),
        )
      : rows;
    const dir = sort.dir === "asc" ? 1 : -1;
    return [...list].sort((a, b) => {
      const va = sortValue(a, sort.key);
      const vb = sortValue(b, sort.key);
      if (va < vb) return -1 * dir;
      if (va > vb) return 1 * dir;
      return 0;
    });
  }, [rows, search, sort]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const current = Math.min(page, totalPages);
  const pageRows = filtered.slice((current - 1) * PAGE_SIZE, current * PAGE_SIZE);

  function toggleSort(key: SortKey) {
    setSort((prev) => {
      if (prev.key === key) return { key, dir: prev.dir === "asc" ? "desc" : "asc" };
      const numeric = COLUMNS.find((c) => c.key === key)?.numeric;
      return { key, dir: numeric ? "desc" : "asc" };
    });
    setPage(1);
  }

  function exportCsv() {
    const header = [
      "Episode", "Date", "Title", "Status", "Collection", "Sound / Music", "Effects",
      "Subtitles", "Thumbnail", "Views", "Impressions", "CTR", "Likes", "Subs",
    ];
    const lines = filtered.map((r) =>
      [
        `EP ${pad2(r.episode)}`, r.date, r.title, r.status, r.collection, r.soundMusic, r.effects,
        r.subtitles, r.thumbnail, r.views, r.impressions,
        r.impressions > 0 ? (r.views / r.impressions).toFixed(4) : "0", r.likes, r.subs,
      ]
        .map(csvCell)
        .join(","),
    );
    const blob = new Blob([[header.map(csvCell).join(","), ...lines].join("\n")], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "youtube-master-content.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="dashboard-fade-in rounded-2xl border border-slate-200/80 bg-white/90 shadow-sm backdrop-blur transition-colors dark:border-slate-800 dark:bg-slate-900/70">
      {/* Toolbar */}
      <div className="flex flex-col gap-3 border-b border-slate-200/80 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5 dark:border-slate-800">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold tracking-tight">YouTube Master Content</h3>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            {fmtInt(filtered.length)} of {fmtInt(rows.length)} episodes · click a header to sort
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative min-w-0 flex-1 sm:w-64 sm:flex-none">
            <svg className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" strokeLinecap="round" />
            </svg>
            <input
              type="search"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Filter by title, EP #, sound, effect…"
              aria-label="Filter episodes"
              className={`${inputClass} py-2 pl-9`}
            />
          </div>
          <button type="button" onClick={exportCsv} className={ghostButtonClass} disabled={filtered.length === 0}>
            Export CSV
          </button>
          <button
            type="button"
            onClick={onAdd}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm shadow-indigo-600/30 transition hover:bg-indigo-500 focus:outline-none focus-visible:ring-4 focus-visible:ring-indigo-500/30"
          >
            <span aria-hidden className="text-base leading-none">+</span> New episode
          </button>
        </div>
      </div>

      {/* Table */}
      <div className={`thin-scroll overflow-x-auto transition-opacity duration-300 ${loading ? "opacity-60" : "opacity-100"}`}>
        <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
          <thead className="bg-slate-50/80 dark:bg-slate-900">
            <tr>
              {COLUMNS.map((col) => {
                const active = sort.key === col.key;
                return (
                  <th
                    key={col.key}
                    scope="col"
                    aria-sort={active ? (sort.dir === "asc" ? "ascending" : "descending") : "none"}
                    className={`whitespace-nowrap px-3 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400 ${
                      col.key === "episode" ? "sticky left-0 z-10 bg-slate-50 dark:bg-slate-900" : ""
                    } ${col.numeric ? "text-right" : "text-left"}`}
                  >
                    <button
                      type="button"
                      onClick={() => toggleSort(col.key)}
                      className={`inline-flex items-center gap-1 transition hover:text-slate-900 dark:hover:text-white ${
                        active ? "text-slate-900 dark:text-white" : ""
                      }`}
                    >
                      {col.label}
                      <span className={`text-[10px] transition-transform ${active && sort.dir === "asc" ? "rotate-180" : ""} ${active ? "opacity-100" : "opacity-30"}`} aria-hidden>
                        ▼
                      </span>
                    </button>
                  </th>
                );
              })}
              <th scope="col" className="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Actions
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {pageRows.map((r) => {
              const color = collectionColor(r.collection);
              const ctr = r.impressions > 0 ? r.views / r.impressions : 0;
              return (
                <tr key={r.id} className="group transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <td className="sticky left-0 z-10 whitespace-nowrap bg-white px-3 py-3 font-semibold tabular-nums transition-colors group-hover:bg-slate-50 dark:bg-slate-900 dark:group-hover:bg-slate-800/50">
                    EP {pad2(r.episode)}
                  </td>
                  <td className="whitespace-nowrap px-3 py-3 text-slate-600 dark:text-slate-300">
                    {formatDateLong(r.date)}
                  </td>
                  <td className="max-w-[260px] px-3 py-3">
                    <p className="truncate font-medium text-slate-900 dark:text-slate-100" title={r.title}>
                      {r.title}
                    </p>
                    <p className="text-xs text-slate-400">{fmtDuration(r.durationSec)} Short</p>
                  </td>
                  <td className="px-3 py-3">
                    <select
                      aria-label={`Status for episode ${r.episode}`}
                      value={r.status}
                      onChange={(e) => onStatusChange(r.id, e.target.value)}
                      className="cursor-pointer rounded-lg border border-slate-200 bg-white py-1 pl-2 pr-6 text-xs font-semibold outline-none transition focus:ring-4 focus:ring-indigo-500/15 dark:border-slate-700 dark:bg-slate-900"
                      style={{ color: STATUS_COLORS[r.status] ?? undefined }}
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s} className="text-slate-900">
                          {s}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="whitespace-nowrap px-3 py-3">
                    <span
                      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
                      style={{ background: `${color}1f`, color }}
                    >
                      <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
                      {r.collection}
                    </span>
                  </td>
                  <td className="max-w-[180px] truncate px-3 py-3 text-slate-600 dark:text-slate-300" title={r.soundMusic}>
                    {r.soundMusic}
                  </td>
                  <td className="max-w-[180px] truncate px-3 py-3 text-slate-600 dark:text-slate-300" title={r.effects}>
                    {r.effects}
                  </td>
                  <td className="whitespace-nowrap px-3 py-3">
                    <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                      {r.subtitles}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-2">
                      {r.hasVideo ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={`/api/content/${r.id}/thumbnail`}
                          alt={`Frame from episode ${r.episode}`}
                          loading="lazy"
                          className="h-9 w-16 shrink-0 rounded-md object-cover shadow-inner"
                        />
                      ) : (
                        <div
                          className="relative h-9 w-16 shrink-0 overflow-hidden rounded-md shadow-inner"
                          style={{ background: `linear-gradient(135deg, ${color}, #0f172a)` }}
                          title={r.thumbnail}
                          aria-label={`Thumbnail ${r.thumbnail}`}
                        >
                          <span className="absolute inset-0 flex items-center justify-center font-mono text-[10px] font-bold text-white/90">
                            #{pad2(r.episode)}
                          </span>
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-3 py-3">
                    <RenderCell row={r} onRender={onRender} onPreview={onPreview} />
                  </td>
                  <td className="whitespace-nowrap px-3 py-3 text-right font-semibold tabular-nums">{fmtCompact(r.views)}</td>
                  <td className="whitespace-nowrap px-3 py-3 text-right tabular-nums text-slate-600 dark:text-slate-300">{fmtPct(ctr)}</td>
                  <td className="whitespace-nowrap px-3 py-3 text-right tabular-nums text-slate-600 dark:text-slate-300">{fmtCompact(r.likes)}</td>
                  <td className="whitespace-nowrap px-3 py-3 text-right tabular-nums text-slate-600 dark:text-slate-300">{fmtInt(r.subs)}</td>
                  <td className="whitespace-nowrap px-3 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => onDelete(r)}
                      aria-label={`Delete episode ${r.episode}`}
                      className="rounded-lg p-1.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-500/10 dark:hover:text-rose-400"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
                      </svg>
                    </button>
                  </td>
                </tr>
              );
            })}
            {pageRows.length === 0 && (
              <tr>
                <td colSpan={COLUMNS.length + 1} className="px-4 py-14 text-center text-sm text-slate-500 dark:text-slate-400">
                  No episodes match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex flex-col items-center justify-between gap-3 border-t border-slate-200/80 px-4 py-3 text-sm sm:flex-row sm:px-5 dark:border-slate-800">
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Page {current} of {totalPages}
        </p>
        <div className="flex items-center gap-2">
          <button type="button" className={ghostButtonClass} onClick={() => setPage(Math.max(1, current - 1))} disabled={current <= 1}>
            ← Prev
          </button>
          <button
            type="button"
            className={ghostButtonClass}
            onClick={() => setPage(Math.min(totalPages, current + 1))}
            disabled={current >= totalPages}
          >
            Next →
          </button>
        </div>
      </div>
    </section>
  );
}
