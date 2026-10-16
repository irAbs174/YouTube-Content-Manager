"use client";
import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import { StudioNav } from "@/components/studio-nav";
import type { ContentRow, EpisodeScene } from "@/lib/types";
import Link from "next/link";

export default function EmulatorPlayer() {
  const { id } = useParams<{ id: string }>();
  const [row, setRow] = useState<ContentRow | null>(null);
  const [scenes, setScenes] = useState<EpisodeScene[]>([]);
  const [playing, setPlaying] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<any>(null);

  useEffect(() => {
    fetch("/api/dashboard", { credentials: "include" }).then((r) => r.json()).then((d) => {
      const found = (d.rows as ContentRow[]).find((r) => String(r.id) === id);
      if (found) setRow(found);
    });
    fetch(`/api/content/${id}/scenes`, { credentials: "include" }).then((r) => r.ok ? r.json() : []).then((sc: EpisodeScene[]) => {
      if (sc.length) setScenes(sc);
    });
  }, [id]);

  useEffect(() => {
    // if no scenes, derive one from script
    if (row && scenes.length === 0 && row.script) {
      setScenes([{ id: 0, position: 0, durationSec: row.durationSec, command: row.script.command, tip: row.script.tip, audio: row.script.audio, notes: "" }]);
    }
  }, [row, scenes.length]);

  const total = scenes.reduce((s, c) => s + c.durationSec, 0) || row?.durationSec || 45;
  const currentIdx = (() => {
    let acc = 0;
    for (let i = 0; i < scenes.length; i++) {
      if (elapsed < acc + scenes[i].durationSec) return i;
      acc += scenes[i].durationSec;
    }
    return Math.max(0, scenes.length - 1);
  })();
  const current = scenes[currentIdx];

  useEffect(() => {
    if (!playing) return;
    timerRef.current = setInterval(() => {
      setElapsed((e) => {
        if (e + 0.2 >= total) { setPlaying(false); return total; }
        return e + 0.2;
      });
    }, 200);
    return () => clearInterval(timerRef.current);
  }, [playing, total]);

  function toggle() {
    if (elapsed >= total) setElapsed(0);
    setPlaying((p) => !p);
  }
  function seek(p: number) {
    setElapsed(p);
  }

  if (!row) return <><StudioNav /><div className="p-6 text-sm text-slate-500">Loading…</div></>;

  return (
    <>
      <StudioNav />
      <main className="mx-auto max-w-6xl p-4 flex flex-col lg:flex-row gap-6">
        <div className="flex flex-1 justify-center">
          <div className="relative h-[700px] w-[360px] overflow-hidden rounded-[2rem] border-[12px] border-slate-900 bg-[#0b1020] shadow-2xl">
            <div className="absolute inset-x-0 top-0 flex items-center justify-between px-3 py-2 text-[11px] text-white/80 bg-black/30">
              <span className="font-medium">{row.seriesName} {row.episodeDisplay}</span>
              <span className="text-[10px]">{row.title.slice(0, 24)}</span>
            </div>
            <div className="flex h-full items-center justify-center p-6 text-center">
              <div className="w-full space-y-4">
                <div className="rounded-xl bg-black/50 px-4 py-4 backdrop-blur">
                  <div className="font-mono text-xl font-bold text-white">❯ {current?.command || row.script?.command || "—"}</div>
                  {(current?.tip || row.script?.tip) && <div className="mt-3 text-sm text-slate-200">{current?.tip || row.script?.tip}</div>}
                  {current?.notes && <div className="mt-2 text-xs text-slate-400">{current.notes}</div>}
                </div>
                <div className="text-[11px] text-white/60">Scene {currentIdx + 1}/{scenes.length || 1} · {current?.durationSec || total}s</div>
              </div>
            </div>
            <div className="absolute inset-x-0 bottom-0 bg-black/60 p-2">
              <div className="mb-2 h-1.5 w-full overflow-hidden rounded-full bg-white/20">
                <div className="h-full bg-white transition-all" style={{ width: `${(elapsed / total) * 100}%` }} />
              </div>
              <div className="flex items-center justify-between text-white">
                <button onClick={toggle} className="rounded-full bg-white px-4 py-1.5 text-xs font-bold text-slate-900">{playing ? "⏸ Pause" : "▶ Play"}</button>
                <span className="text-[11px] tabular-nums">{Math.floor(elapsed)}s / {total}s</span>
                <Link href={`/lab/${row.id}`} className="text-[11px] underline opacity-80">Edit in Lab</Link>
              </div>
              <div className="mt-2 flex gap-1 overflow-x-auto">
                {scenes.map((sc, idx) => (
                  <button key={sc.id} onClick={() => setElapsed(scenes.slice(0, idx).reduce((s, c) => s + c.durationSec, 0))} className={`whitespace-nowrap rounded-full px-2 py-1 text-[10px] ${idx === currentIdx ? "bg-white text-slate-900" : "bg-white/20 text-white"}`}>SCN{idx + 1}</button>
                ))}
              </div>
            </div>
          </div>
        </div>
        <div className="w-full max-w-sm space-y-4">
          <div className="rounded-2xl border bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-sm font-semibold">{row.episodeDisplay}</h2>
            <p className="text-sm text-slate-500">{row.title}</p>
            <div className="mt-2 flex gap-2 text-xs">
              <span className={`rounded-full px-2 py-1 ${row.visibility === "Public" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{row.visibility}</span>
              <span className="rounded-full bg-slate-100 px-2 py-1">{row.collection || "—"}</span>
            </div>
            <input type="range" min={0} max={total} value={elapsed} onChange={(e) => seek(Number(e.target.value))} className="mt-4 w-full" />
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div>Sound FX: {row.soundEffects ? "✓" : "—"}</div>
              <div>Music: {row.music ? "✓" : "—"}</div>
              <div>Subtitles: {row.subtitlesCount}</div>
              <div>Thumbnail: {row.thumbnailReady ? "✓" : "—"}</div>
            </div>
          </div>
          <Link href="/emulator" className="block text-center text-xs text-slate-500 underline">← Back to picker</Link>
        </div>
      </main>
    </>
  );
}
