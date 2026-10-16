"use client";
import { useEffect, useState } from "react";
import { StudioNav } from "@/components/studio-nav";
import Link from "next/link";
import type { ContentRow } from "@/lib/types";

export default function EmulatorPicker() {
  const [rows, setRows] = useState<ContentRow[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    fetch("/api/dashboard", { credentials: "include" }).then((r) => r.json()).then((d) => { setRows(d.rows || []); setLoading(false); }).catch(() => setLoading(false));
  }, []);
  const grouped = rows.reduce<Record<string, ContentRow[]>>((acc, r) => {
    const key = r.seriesName || "General";
    (acc[key] ||= []).push(r);
    return acc;
  }, {});
  return (
    <>
      <StudioNav />
      <main className="mx-auto max-w-5xl p-4 sm:p-6 space-y-6">
        <h1 className="text-xl font-semibold">Emulator</h1>
        <p className="text-sm text-slate-500">Pick an episode to preview in live 9:16 Shorts chrome — no FFmpeg, just timed scene playback.</p>
        {loading ? <div className="text-sm text-slate-500">Loading…</div> : Object.entries(grouped).map(([series, episodes]) => (
          <div key={series} className="rounded-2xl border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-sm font-semibold">{series} · {episodes.length}</h2>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {episodes.map((ep) => (
                <Link key={ep.id} href={`/emulator/${ep.id}`} className="flex items-center justify-between rounded-xl border px-3 py-2 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800">
                  <div>
                    <div className="text-sm font-medium">{ep.episodeDisplay} · {ep.title.slice(0, 40)}</div>
                    <div className="text-xs text-slate-500">{ep.visibility} · {ep.durationSec}s · {ep.scenes.length || 1} scene(s)</div>
                  </div>
                  <span className="text-xs">▶</span>
                </Link>
              ))}
            </div>
          </div>
        ))}
        {!loading && rows.length === 0 && <div className="text-sm text-slate-500">No episodes — create one in the Lab.</div>}
      </main>
    </>
  );
}
