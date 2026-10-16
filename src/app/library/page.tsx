"use client";
import { useEffect, useState } from "react";
import { StudioNav } from "@/components/studio-nav";
import type { ContentRow } from "@/lib/types";
import Link from "next/link";

type Tab = "youtubeMain" | "scenes" | "meta";

export default function LibraryPage() {
  const [tab, setTab] = useState<Tab>("youtubeMain");
  const [rows, setRows] = useState<ContentRow[]>([]);
  const [series, setSeries] = useState<any[]>([]);
  const [collections, setCollections] = useState<any[]>([]);
  const [scenes, setScenes] = useState<any[]>([]);
  const [filterSeries, setFilterSeries] = useState("All");
  const [filterVisibility, setFilterVisibility] = useState("All");

  useEffect(() => {
    fetch("/api/dashboard", { credentials: "include" }).then((r) => r.json()).then((d) => setRows(d.rows || []));
    fetch("/api/series", { credentials: "include" }).then((r) => r.json()).then(setSeries).catch(() => {});
    fetch("/api/meta", { credentials: "include" }).then((r) => r.json()).then((m) => setCollections(m.collections || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (tab === "scenes" && rows.length) {
      // fetch scenes for each row (limit first 10 to avoid spam)
      Promise.all(rows.slice(0, 20).map((r) => fetch(`/api/content/${r.id}/scenes`, { credentials: "include" }).then((x) => (x.ok ? x.json() : [])).then((sc) => sc.map((s: any) => ({ ...s, episodeDisplay: r.episodeDisplay, seriesName: r.seriesName }))))).then((all) => setScenes(all.flat()));
    }
  }, [tab, rows]);

  const filtered = rows.filter((r) => {
    if (filterSeries !== "All" && r.seriesName !== filterSeries) return false;
    if (filterVisibility !== "All" && r.visibility !== filterVisibility) return false;
    return true;
  });

  return (
    <>
      <StudioNav />
      <main className="mx-auto max-w-7xl p-4 sm:p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h1 className="text-xl font-semibold">Library</h1>
          <div className="flex gap-1 rounded-full bg-slate-100 p-1 dark:bg-slate-800">
            {(["youtubeMain", "scenes", "meta"] as Tab[]).map((t) => (
              <button key={t} onClick={() => setTab(t)} className={`rounded-full px-3 py-1 text-xs font-medium ${tab === t ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900" : "text-slate-600"}`}>{t === "youtubeMain" ? "YouTube Main" : t === "scenes" ? "Scenes" : "Meta"}</button>
            ))}
          </div>
        </div>

        {tab === "youtubeMain" && (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2 text-xs">
              <select value={filterSeries} onChange={(e) => setFilterSeries(e.target.value)} className="rounded border px-2 py-1">
                <option value="All">All series</option>
                {[...new Set(rows.map((r) => r.seriesName))].map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <select value={filterVisibility} onChange={(e) => setFilterVisibility(e.target.value)} className="rounded border px-2 py-1">
                <option value="All">All visibility</option>
                <option value="Public">Public</option>
                <option value="Private">Private</option>
              </select>
              <span className="ml-auto text-slate-500">{filtered.length} rows</span>
            </div>
            <div className="overflow-x-auto rounded-xl border bg-white dark:border-slate-800 dark:bg-slate-900">
              <table className="min-w-full text-xs">
                <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 dark:bg-slate-800">
                  <tr>
                    <th className="px-3 py-2 text-left">Episode</th>
                    <th className="px-3 py-2">Date</th>
                    <th className="px-3 py-2 text-left">Title</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Collection</th>
                    <th className="px-3 py-2">Sound FX</th>
                    <th className="px-3 py-2">Music</th>
                    <th className="px-3 py-2">Subtitles</th>
                    <th className="px-3 py-2">Thumbnail</th>
                    <th className="px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r) => (
                    <tr key={r.id} className="border-t hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-3 py-2 font-medium">{r.episodeDisplay}</td>
                      <td className="px-3 py-2">{r.date}</td>
                      <td className="px-3 py-2 max-w-[280px] truncate">{r.title}</td>
                      <td className="px-3 py-2"><span className={`rounded-full px-2 py-0.5 text-[10px] ${r.visibility === "Public" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{r.visibility}</span></td>
                      <td className="px-3 py-2">{r.collection || "—"}</td>
                      <td className="px-3 py-2 text-center">{r.soundEffects ? "✓" : "—"}</td>
                      <td className="px-3 py-2 text-center">{r.music ? "✓" : "—"}</td>
                      <td className="px-3 py-2 text-center">{r.subtitlesCount}</td>
                      <td className="px-3 py-2 text-center">{r.thumbnailReady ? "✓" : "—"}</td>
                      <td className="px-3 py-2">
                        <div className="flex gap-1">
                          <Link href={`/lab/${r.id}`} className="rounded border px-2 py-1 text-[10px]">Lab</Link>
                          <Link href={`/emulator/${r.id}`} className="rounded border px-2 py-1 text-[10px]">Emu</Link>
                          <a href={`/api/content/${r.id}/video`} target="_blank" className="rounded bg-slate-900 px-2 py-1 text-[10px] text-white">Video</a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {tab === "scenes" && (
          <div className="rounded-xl border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-sm font-semibold">Scenes — flat list</h2>
            <div className="mt-3 space-y-1 text-xs">
              {scenes.length === 0 ? <div className="text-slate-500">No scenes yet — Lab will create them.</div> : scenes.map((s) => (
                <div key={s.id} className="flex gap-2 rounded border px-2 py-1">
                  <span className="font-medium">{s.episodeDisplay} · SCN{s.position + 1}</span>
                  <span className="truncate">{s.command}</span>
                  <span className="ml-auto text-slate-500">{s.durationSec}s</span>
                  <Link href={`/lab/${s.content_id || s.contentId || ""}`} className="underline">Lab</Link>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "meta" && (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
              <h3 className="text-sm font-semibold">Series</h3>
              <div className="mt-2 space-y-1 text-sm">
                {series.map((s) => <div key={s.id} className="flex justify-between border-b py-1"><span>{s.name}</span><span className="text-slate-500">{s.episodeCount}</span></div>)}
                {series.length === 0 && <div className="text-xs text-slate-500">No series.</div>}
              </div>
            </div>
            <div className="rounded-xl border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
              <h3 className="text-sm font-semibold">Collections</h3>
              <div className="mt-2 space-y-1 text-sm">
                {collections.map((c) => <div key={c.name} className="flex items-center gap-2 border-b py-1"><span className="h-3 w-3 rounded-full" style={{ background: c.color }} /><span>{c.name}</span></div>)}
              </div>
            </div>
            <div className="rounded-xl border bg-white p-4 dark:border-slate-800 dark:bg-slate-900 sm:col-span-2">
              <h3 className="text-sm font-semibold">Visibility counts</h3>
              <div className="mt-2 flex gap-4 text-sm">
                <span>Public: {rows.filter((r) => r.visibility === "Public").length}</span>
                <span>Private: {rows.filter((r) => r.visibility === "Private").length}</span>
              </div>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
