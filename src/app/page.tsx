"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { StudioNav } from "@/components/studio-nav";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import type { DashboardData } from "@/lib/types";
import Link from "next/link";

export default function HomePage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [authed, setAuthed] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("/api/auth/me", { credentials: "include" })
      .then((r) => {
        if (!r.ok) {
          router.push("/login");
          setAuthed(false);
          return null;
        }
        setAuthed(true);
        return r.json();
      })
      .then(() => {
        // fetch dashboard after auth check
        return fetch("/api/dashboard", { credentials: "include", cache: "no-store" }).then((r) => r.json());
      })
      .then((json) => {
        if (json) setData(json);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [router]);

  if (authed === false) return null;

  if (loading || !data) {
    return (
      <>
        <StudioNav />
        <div className="mx-auto max-w-6xl p-6 text-sm text-slate-500">Loading studio…</div>
      </>
    );
  }

  const publicCount = data.rows.filter((r) => r.visibility === "Public" || r.status === "Public").length;
  const privateCount = data.rows.filter((r) => r.visibility === "Private" || r.status === "Private").length;
  const thumbReady = data.rows.filter((r) => r.thumbnailReady).length;
  const soundReady = data.rows.filter((r) => r.soundEffects).length;
  const musicReady = data.rows.filter((r) => r.music).length;

  return (
    <>
      <StudioNav />
      <main className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Home</h1>
          <p className="text-sm text-slate-500">Minimal hub — KPIs, visibility, and quick jumps to Lab / Emulator / Library.</p>
        </div>

        <KpiCards data={data} />

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="text-xs font-medium text-slate-500">Visibility</div>
            <div className="mt-2 flex gap-4">
              <div>
                <div className="text-2xl font-semibold text-emerald-600">{publicCount}</div>
                <div className="text-xs text-slate-500">Public</div>
              </div>
              <div>
                <div className="text-2xl font-semibold text-slate-400">{privateCount}</div>
                <div className="text-xs text-slate-500">Private</div>
              </div>
            </div>
          </div>
          <div className="rounded-2xl border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="text-xs font-medium text-slate-500">Readiness</div>
            <div className="mt-2 space-y-1 text-sm">
              <div className="flex justify-between"><span>Thumbnail</span><span className="font-medium">{thumbReady}/{data.rows.length}</span></div>
              <div className="flex justify-between"><span>Sound FX</span><span className="font-medium">{soundReady}/{data.rows.length}</span></div>
              <div className="flex justify-between"><span>Music</span><span className="font-medium">{musicReady}/{data.rows.length}</span></div>
            </div>
          </div>
          <div className="rounded-2xl border bg-gradient-to-br from-slate-900 to-slate-700 p-4 text-white dark:from-white dark:to-slate-200 dark:text-slate-900">
            <div className="text-xs font-medium opacity-80">Destinations</div>
            <div className="mt-3 grid gap-2">
              <Link href="/lab" className="rounded-lg bg-white/10 px-3 py-2 text-sm font-medium hover:bg-white/20 dark:bg-slate-900/10 dark:hover:bg-slate-900/20">+ New in Lab →</Link>
              <Link href="/emulator" className="rounded-lg bg-white/10 px-3 py-2 text-sm font-medium hover:bg-white/20">Preview in Emulator →</Link>
              <Link href="/library" className="rounded-lg bg-white/10 px-3 py-2 text-sm font-medium hover:bg-white/20">Browse Library →</Link>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Recent episodes</h2>
            <Link href="/library" className="text-xs text-slate-500 underline">View all</Link>
          </div>
          <div className="mt-3 space-y-2">
            {data.rows.slice(0, 3).map((row) => (
              <Link key={row.id} href={`/lab/${row.id}`} className="flex items-center justify-between rounded-lg border px-3 py-2 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{row.episodeDisplay} · {row.title}</div>
                  <div className="text-xs text-slate-500">{row.date} · {row.visibility}</div>
                </div>
                <div className={`h-2 w-2 shrink-0 rounded-full ${row.visibility === "Public" ? "bg-emerald-500" : "bg-slate-300"}`} />
              </Link>
            ))}
            {data.rows.length === 0 && <div className="text-sm text-slate-500">No episodes yet — create your first in the Lab.</div>}
          </div>
        </div>
      </main>
    </>
  );
}
