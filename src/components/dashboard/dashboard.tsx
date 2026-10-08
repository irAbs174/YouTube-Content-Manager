"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  COLLECTIONS,
  LIVE_INTERVAL_MS,
  PRESET_DAYS,
  STATUSES,
  STATUS_COLORS,
  collectionColor,
  type Preset,
} from "@/lib/constants";
import { addDays, formatDateLong, formatDayLabel, todayISO, weekStart } from "@/lib/dates";
import { fmtCompact, pad2, shorten } from "@/lib/format";
import type { ContentRow, DashboardData, RenderState, SeriesPoint } from "@/lib/types";
import { AddEpisodeDialog } from "./add-episode-dialog";
import { VideoPreviewDialog } from "./video-preview-dialog";
import { CollectionBars, StatusDonut, TopEpisodesBars, TrendChart, type BarDatum, type MixSlice, type TrendPoint } from "./charts";
import { ContentTable } from "./content-table";
import { FiltersBar } from "./filters-bar";
import { KpiCards } from "./kpi-cards";
import { ThemeToggle } from "./theme-toggle";
import { Panel } from "./ui";

interface DashboardProps {
  initialData: DashboardData;
}

/** Buckets daily points into weekly totals for long ranges (keeps the trend readable). */
function bucketSeries(series: SeriesPoint[], weekly: boolean): TrendPoint[] {
  const map = new Map<string, { day: string; views: number; subs: number }>();
  for (const p of series) {
    const key = weekly ? weekStart(p.day) : p.day;
    const bucket = map.get(key) ?? { day: key, views: 0, subs: 0 };
    bucket.views += p.views;
    bucket.subs += p.subs;
    map.set(key, bucket);
  }
  return [...map.values()].map((b) => ({
    ...b,
    label: weekly ? `Wk ${formatDayLabel(b.day)}` : formatDayLabel(b.day),
  }));
}

export function Dashboard({ initialData }: DashboardProps) {
  // ── filter state ──────────────────────────────────────────────────────────
  const [preset, setPreset] = useState<Preset>("90D");
  const [from, setFrom] = useState(initialData.range.from);
  const [to, setTo] = useState(initialData.range.to);
  const [collection, setCollection] = useState("All");
  const [status, setStatus] = useState("All");

  // ── data state ────────────────────────────────────────────────────────────
  const [data, setData] = useState<DashboardData>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [live, setLive] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // ── UI state ──────────────────────────────────────────────────────────────
  const [addOpen, setAddOpen] = useState(false);
  const [notice, setNotice] = useState<{ text: string; at: number } | null>(null);
  const [preview, setPreview] = useState<ContentRow | null>(null);

  const initialKey = useRef(`${initialData.range.from}|${initialData.range.to}|All|All`).current;
  const fetchKey = `${from}|${to}|${collection}|${status}`;
  const firstRun = useRef(true);

  // Fetch whenever a filter changes (or a manual / live refresh is requested).
  useEffect(() => {
    if (firstRun.current) {
      firstRun.current = false;
      // Server rendered exactly this view — skip the redundant first request.
      if (fetchKey === initialKey && reloadKey === 0) return;
    }

    const controller = new AbortController();
    (async () => {
      setLoading(true);
      try {
        const qs = new URLSearchParams({ from, to, collection, status });
        const res = await fetch(`/api/dashboard?${qs.toString()}`, {
          signal: controller.signal,
          cache: "no-store",
        });
        if (!res.ok) throw new Error(`Request failed (${res.status})`);
        const json = (await res.json()) as DashboardData;
        setData(json);
        setError(null);
        setLastUpdated(new Date());
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError("Could not refresh analytics. Check the database connection and try again.");
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();

    return () => controller.abort();
  }, [fetchKey, reloadKey, from, to, collection, status, initialKey]);

  // Live refresh.
  useEffect(() => {
    if (!live) return;
    const id = window.setInterval(() => setReloadKey((k) => k + 1), LIVE_INTERVAL_MS);
    return () => window.clearInterval(id);
  }, [live]);

  // Transient toast.
  useEffect(() => {
    if (!notice) return;
    const t = window.setTimeout(() => setNotice(null), 2600);
    return () => window.clearTimeout(t);
  }, [notice]);

  const flash = useCallback((text: string) => setNotice({ text, at: Date.now() }), []);
  const closeAdd = useCallback(() => setAddOpen(false), []);
  const refresh = useCallback(() => setReloadKey((k) => k + 1), []);

  // ── FFmpeg render progress ────────────────────────────────────────────────
  const activeIds = useMemo(
    () => data.rows.filter((r) => r.renderStatus === "queued" || r.renderStatus === "running").map((r) => r.id),
    [data.rows],
  );
  const activeKey = activeIds.join(",");

  // While renders are in flight, poll the lightweight status endpoint every 1.5s.
  // When a render finishes, do one full refresh so charts and the table pick it up.
  useEffect(() => {
    if (!activeKey) return;
    let stopped = false;
    const tick = async () => {
      try {
        const res = await fetch(`/api/renders?ids=${activeKey}`, { cache: "no-store" });
        if (!res.ok || stopped) return;
        const states = (await res.json()) as RenderState[];
        if (stopped) return;
        setData((prev) => ({
          ...prev,
          rows: prev.rows.map((r) => {
            const s = states.find((x) => x.id === r.id);
            return s
              ? {
                  ...r,
                  renderStatus: s.renderStatus,
                  renderProgress: s.renderProgress,
                  renderError: s.renderError,
                  hasVideo: s.hasVideo,
                }
              : r;
          }),
        }));
        if (states.some((s) => s.renderStatus !== "queued" && s.renderStatus !== "running")) refresh();
      } catch {
        /* transient network error — next tick retries */
      }
    };
    void tick();
    const id = window.setInterval(tick, 1500);
    return () => {
      stopped = true;
      window.clearInterval(id);
    };
  }, [activeKey, refresh]);

  async function renderEpisode(row: ContentRow) {
    try {
      const res = await fetch(`/api/content/${row.id}/render`, { method: "POST" });
      const json = (await res.json().catch(() => ({}))) as { error?: string };
      if (!res.ok) throw new Error(json.error ?? "Could not queue render");
      setData((prev) => ({
        ...prev,
        rows: prev.rows.map((r) =>
          r.id === row.id ? { ...r, renderStatus: "queued", renderProgress: 0, renderError: null } : r,
        ),
      }));
      flash(`Rendering EP ${pad2(row.episode)} with FFmpeg…`);
    } catch (err) {
      flash(err instanceof Error ? err.message : "Could not queue render");
    }
  }

  // ── filter handlers ───────────────────────────────────────────────────────
  function applyPreset(p: Preset) {
    setPreset(p);
    if (p === "Custom") return;
    const end = todayISO();
    setTo(end);
    setFrom(addDays(end, -(PRESET_DAYS[p] - 1)));
  }

  function onFrom(v: string) {
    setPreset("Custom");
    setFrom(v);
    if (v > to) setTo(v);
  }

  function onTo(v: string) {
    setPreset("Custom");
    setTo(v);
    if (v < from) setFrom(v);
  }

  function resetSegments() {
    setCollection("All");
    setStatus("All");
  }

  // ── mutations ─────────────────────────────────────────────────────────────
  async function changeStatus(id: number, nextStatus: string) {
    setData((prev) => ({
      ...prev,
      rows: prev.rows.map((r) => (r.id === id ? { ...r, status: nextStatus } : r)),
    }));
    try {
      const res = await fetch(`/api/content/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (!res.ok) throw new Error();
      flash("Status updated");
    } catch {
      flash("Could not update status");
    }
    refresh();
  }

  async function removeRow(row: ContentRow) {
    if (!window.confirm(`Delete EP ${pad2(row.episode)} “${row.title}”? Its analytics will be removed too.`)) return;
    try {
      const res = await fetch(`/api/content/${row.id}`, { method: "DELETE" });
      if (!res.ok) throw new Error();
      flash("Episode deleted");
    } catch {
      flash("Could not delete episode");
    }
    refresh();
  }

  // ── derived view data (all charts recompute from the live dataset) ───────
  const rows = data.rows;
  const weekly = data.range.days > 120;

  const trend = useMemo(() => bucketSeries(data.series, weekly), [data.series, weekly]);

  const collectionBars = useMemo<BarDatum[]>(
    () =>
      COLLECTIONS.map((c) => {
        const list = rows.filter((r) => r.collection === c.name);
        return {
          name: c.name,
          value: list.reduce((sum, r) => sum + r.views, 0),
          color: c.color,
          episodes: list.length,
        };
      })
        .filter((c) => c.episodes > 0)
        .sort((a, b) => b.value - a.value)
        .map(({ name, value, color }) => ({ name, value, color })),
    [rows],
  );

  const statusMix = useMemo<MixSlice[]>(
    () =>
      STATUSES.map((s) => ({
        name: s,
        value: rows.filter((r) => r.status === s).length,
        color: STATUS_COLORS[s],
      })).filter((s) => s.value > 0),
    [rows],
  );

  const topEpisodes = useMemo<BarDatum[]>(
    () =>
      [...rows]
        .filter((r) => r.views > 0)
        .sort((a, b) => b.views - a.views)
        .slice(0, 8)
        .map((r) => ({
          name: `EP ${pad2(r.episode)} · ${shorten(r.title, 22)}`,
          value: r.views,
          color: collectionColor(r.collection),
        })),
    [rows],
  );

  const totalViews = data.kpis.views.value;
  const subtitleText = `${formatDateLong(from)} – ${formatDateLong(to)} · ${
    collection === "All" ? "All segments" : collection
  } · ${status === "All" ? "All statuses" : status}`;

  return (
    <div className="relative min-h-screen">
      {/* Decorative backdrop */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-x-0 top-0 -z-10 h-112 bg-[radial-gradient(55%_60%_at_50%_0%,rgba(99,102,241,0.16),transparent)] dark:bg-[radial-gradient(55%_60%_at_50%_0%,rgba(99,102,241,0.24),transparent)]"
      />

      {/* Loading bar */}
      <div
        aria-hidden
        className={`fixed inset-x-0 top-0 z-50 h-0.5 overflow-hidden bg-transparent transition-opacity duration-300 ${loading ? "opacity-100" : "opacity-0"}`}
      >
        <div className="h-full w-full animate-pulse bg-linear-to-r from-cyan-400 via-indigo-500 to-rose-500" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-slate-200/70 bg-white/75 backdrop-blur-xl transition-colors dark:border-slate-800/80 dark:bg-slate-950/75">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:px-6">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-linear-to-br from-rose-500 to-red-600 text-white shadow-lg shadow-rose-600/30">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold leading-tight sm:text-base">YouTube Master Content</p>
            <p className="hidden truncate text-xs text-slate-500 dark:text-slate-400 sm:block">
              Create / Manage · Shorts analytics
            </p>
          </div>

          <div className="ml-auto flex items-center gap-2 sm:gap-3">
            {activeIds.length > 0 && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700 dark:border-indigo-500/30 dark:bg-indigo-500/10 dark:text-indigo-300">
                <span className="h-2 w-2 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" aria-hidden />
                Rendering {activeIds.length}
              </span>
            )}

            <button
              type="button"
              onClick={() => setLive((v) => !v)}
              aria-pressed={live}
              title={live ? `Auto-refreshing every ${LIVE_INTERVAL_MS / 1000}s` : "Auto-refresh paused"}
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                live
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300"
                  : "border-slate-200 bg-white text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
              }`}
            >
              <span className="relative flex h-2 w-2" aria-hidden>
                {live && <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75" />}
                <span className={`relative inline-flex h-2 w-2 rounded-full ${live ? "bg-emerald-500" : "bg-slate-400"}`} />
              </span>
              {live ? "Live" : "Paused"}
            </button>

            <button
              type="button"
              onClick={() => setAddOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 px-3 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700 focus:outline-none focus-visible:ring-4 focus-visible:ring-indigo-500/30 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
            >
              <span aria-hidden className="text-base leading-none">+</span>
              <span className="hidden sm:inline">New episode</span>
              <span className="sm:hidden">New</span>
            </button>

            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-4 pb-20 pt-6 sm:px-6 md:pt-8">
        {/* Title row */}
        <div className="dashboard-fade-in flex flex-wrap items-end justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Channel overview</h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitleText}</p>
          </div>
          <p className="hidden text-xs text-slate-500 dark:text-slate-400 md:block" aria-live="polite">
            {loading ? "Updating…" : lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}` : "Up to date"}
          </p>
        </div>

        <FiltersBar
          preset={preset}
          from={from}
          to={to}
          days={data.range.days}
          collection={collection}
          status={status}
          onPreset={applyPreset}
          onFrom={onFrom}
          onTo={onTo}
          onCollection={setCollection}
          onStatus={setStatus}
          onReset={resetSegments}
        />

        {error && (
          <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300">
            {error}
          </div>
        )}

        <div className={`space-y-6 transition-opacity duration-300 ${loading ? "opacity-70" : "opacity-100"}`}>
          <KpiCards data={data} />

          <div className="grid gap-6 xl:grid-cols-3">
            <Panel
              className="xl:col-span-2"
              title="Views & subscribers"
              subtitle={weekly ? "Weekly totals — range exceeds 120 days" : "Daily totals across the selected segment"}
            >
              <TrendChart points={trend} />
            </Panel>

            <Panel
              title="Status mix"
              subtitle={`${rows.length} episodes in view · ${fmtCompact(totalViews)} views`}
            >
              <StatusDonut data={statusMix} total={rows.length} />
            </Panel>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Panel title="Views by collection" subtitle="Click a segment chip above to drill down">
              <CollectionBars data={collectionBars} />
            </Panel>
            <Panel title="Top episodes" subtitle="Highest views in the selected range">
              <TopEpisodesBars data={topEpisodes} />
            </Panel>
          </div>

          <ContentTable
            rows={rows}
            loading={loading}
            onAdd={() => setAddOpen(true)}
            onStatusChange={changeStatus}
            onDelete={removeRow}
            onRender={renderEpisode}
            onPreview={setPreview}
          />
        </div>

        <footer className="pt-4 text-center text-xs text-slate-400 dark:text-slate-500">
          Sample data · {data.series.length} days · generated {new Date(data.generatedAt).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" })} (UTC)
        </footer>
      </main>

      {addOpen && (
        <AddEpisodeDialog
          onClose={closeAdd}
          onCreated={() => {
            flash("Episode created · rendering with FFmpeg");
            refresh();
          }}
        />
      )}

      {preview && <VideoPreviewDialog row={preview} onClose={() => setPreview(null)} />}

      {notice && (
        <div
          key={notice.at}
          role="status"
          className="dashboard-fade-in fixed bottom-4 left-1/2 z-[60] -translate-x-1/2 rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-xl dark:bg-white dark:text-slate-900"
        >
          {notice.text}
        </div>
      )}
    </div>
  );
}
