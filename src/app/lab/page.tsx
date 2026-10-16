"use client";

import { useEffect, useState } from "react";
import { StudioNav } from "@/components/studio-nav";
import { useRouter } from "next/navigation";
import type { EpisodeScene } from "@/lib/types";

interface SeriesInfo { id: number; name: string; episodeCount: number; }
interface CollectionInfo { name: string; color: string; sounds: string[]; }

export default function LabNewPage() {
  const router = useRouter();
  const [seriesList, setSeriesList] = useState<SeriesInfo[]>([]);
  const [collections, setCollections] = useState<CollectionInfo[]>([]);
  const [title, setTitle] = useState("");
  const [seriesName, setSeriesName] = useState("");
  const [episodeNumber, setEpisodeNumber] = useState<number | "">("");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [visibility, setVisibility] = useState<"Private" | "Public">("Private");
  const [collection, setCollection] = useState("");
  const [soundEffects, setSoundEffects] = useState(false);
  const [music, setMusic] = useState(false);
  const [subtitlesCount, setSubtitlesCount] = useState(0);
  const [thumbnailReady, setThumbnailReady] = useState(false);
  const [scenes, setScenes] = useState<EpisodeScene[]>([
    { id: Date.now(), position: 0, durationSec: 45, command: "", tip: "", audio: true, notes: "" },
  ]);
  const [selected, setSelected] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/series", { credentials: "include" }).then((r) => r.json()).then(setSeriesList).catch(() => {});
    fetch("/api/meta", { credentials: "include" }).then((r) => r.json()).then((m) => setCollections(m.collections || [])).catch(() => {});
  }, []);

  function updateScene(idx: number, patch: Partial<EpisodeScene>) {
    setScenes((prev) => prev.map((s, i) => (i === idx ? { ...s, ...patch } : s)));
  }
  function addScene() {
    const newScene: EpisodeScene = { id: Date.now() + Math.random(), position: scenes.length, durationSec: 15, command: "", tip: "", audio: true, notes: "" };
    setScenes([...scenes, newScene]);
    setSelected(scenes.length);
  }
  function removeScene(idx: number) {
    if (scenes.length <= 1) return;
    setScenes((prev) => prev.filter((_, i) => i !== idx).map((s, i) => ({ ...s, position: i })));
    setSelected(Math.max(0, idx - 1));
  }
  function moveScene(idx: number, dir: number) {
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= scenes.length) return;
    const copy = [...scenes];
    const [moved] = copy.splice(idx, 1);
    copy.splice(newIdx, 0, moved);
    setScenes(copy.map((s, i) => ({ ...s, position: i })));
    setSelected(newIdx);
  }

  async function handleSave(render = false) {
    setError(null);
    setSaving(true);
    try {
      const payload: any = {
        title: title.trim() || "Untitled episode",
        date,
        visibility,
        collection: collection || undefined,
        seriesName: seriesName.trim() || undefined,
        episodeNumber: episodeNumber === "" ? undefined : Number(episodeNumber),
        soundEffects,
        music,
        subtitlesCount,
        thumbnailReady,
        durationSec: scenes.reduce((sum, s) => sum + s.durationSec, 0),
        render,
        command: scenes[0]?.command || "",
        tip: scenes[0]?.tip || "",
        audio: scenes[0]?.audio ?? true,
        scenes: scenes.map((s, i) => ({ position: i, durationSec: s.durationSec, command: s.command, tip: s.tip, audio: s.audio, notes: s.notes })),
      };
      const res = await fetch("/api/content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Failed to save");
      router.push(`/lab/${body.id}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  const current = scenes[selected];

  return (
    <>
      <StudioNav />
      <div className="mx-auto flex max-w-7xl flex-col gap-4 p-4 lg:flex-row lg:gap-6">
        {/* Left — scene stack */}
        <div className="w-full shrink-0 lg:w-[320px] space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Scenes ({scenes.length})</h2>
            <button onClick={addScene} className="rounded-full bg-slate-900 px-3 py-1.5 text-xs font-medium text-white dark:bg-white dark:text-slate-900">+ Add</button>
          </div>
          <div className="space-y-2">
            {scenes.map((sc, idx) => (
              <div key={sc.id} onClick={() => setSelected(idx)} className={`cursor-pointer rounded-xl border p-3 ${selected === idx ? "border-slate-900 bg-slate-50 dark:border-white dark:bg-slate-800" : "bg-white hover:bg-slate-50 dark:bg-slate-900"}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold tracking-widest text-slate-500">SCN{idx + 1}</span>
                  <span className="text-xs text-slate-400">{sc.durationSec}s</span>
                </div>
                <div className="mt-1 truncate text-sm font-medium">{sc.command || "— no command —"}</div>
                <div className="truncate text-xs text-slate-500">{sc.tip || "no tip"}</div>
                <div className="mt-2 flex gap-1">
                  <button onClick={(e) => { e.stopPropagation(); moveScene(idx, -1); }} className="rounded border px-2 py-1 text-[10px]">↑</button>
                  <button onClick={(e) => { e.stopPropagation(); moveScene(idx, 1); }} className="rounded border px-2 py-1 text-[10px]">↓</button>
                  <button onClick={(e) => { e.stopPropagation(); removeScene(idx); }} className="ml-auto rounded px-2 py-1 text-[10px] text-red-600">Delete</button>
                </div>
              </div>
            ))}
          </div>
          {selected >= 0 && current && (
            <div className="rounded-xl border bg-white p-3 dark:bg-slate-900 space-y-2">
              <label className="text-xs font-medium">Command (SCN{selected + 1})</label>
              <input value={current.command} onChange={(e) => updateScene(selected, { command: e.target.value })} placeholder="e.g. nmap -sn 127.0.0.1" className="w-full rounded border px-2 py-1.5 text-sm dark:bg-slate-800" />
              <label className="text-xs font-medium">Tip</label>
              <input value={current.tip} onChange={(e) => updateScene(selected, { tip: e.target.value })} placeholder="Fast tip for this beat" className="w-full rounded border px-2 py-1.5 text-sm dark:bg-slate-800" />
              <div className="flex gap-2">
                <label className="flex items-center gap-1 text-xs"><input type="checkbox" checked={current.audio} onChange={(e) => updateScene(selected, { audio: e.target.checked })} /> Audio</label>
                <label className="flex items-center gap-1 text-xs">Duration <input type="number" value={current.durationSec} min={5} max={180} onChange={(e) => updateScene(selected, { durationSec: Number(e.target.value) })} className="w-16 rounded border px-1 py-0.5 text-xs" /></label>
              </div>
              <label className="text-xs font-medium">Notes</label>
              <textarea value={current.notes} onChange={(e) => updateScene(selected, { notes: e.target.value })} rows={2} className="w-full rounded border px-2 py-1 text-xs dark:bg-slate-800" />
            </div>
          )}
        </div>

        {/* Center — 9:16 stage */}
        <div className="flex flex-1 justify-center">
          <div className="relative h-[640px] w-[360px] overflow-hidden rounded-[2rem] border-[10px] border-slate-900 bg-[#0b1020] shadow-2xl dark:border-slate-700">
            <div className="absolute inset-x-0 top-0 flex items-center justify-between bg-black/40 px-3 py-2 text-[10px] font-medium text-white">
              <span>Shorts</span><span>{seriesName || "Series"} #{episodeNumber || "—"}</span>
            </div>
            <div className="flex h-full flex-col items-center justify-center p-6 text-center">
              <div className="rounded-lg bg-black/40 px-4 py-3 backdrop-blur">
                <div className="font-mono text-lg font-bold text-white">❯ {current?.command || "Type a command"}</div>
                {current?.tip && <div className="mt-3 text-sm text-slate-300">{current.tip}</div>}
              </div>
              <div className="absolute bottom-6 left-3 right-3 flex items-center gap-2">
                <div className="h-1 flex-1 rounded-full bg-white/20">
                  <div className="h-1 rounded-full bg-white" style={{ width: `${((selected + 1) / scenes.length) * 100}%` }} />
                </div>
                <span className="text-[10px] text-white/70">{scenes[selected]?.durationSec ?? 0}s</span>
              </div>
            </div>
            <div className="absolute inset-x-0 bottom-0 flex justify-around bg-black/60 px-2 py-2 text-[10px] text-white/80">
              <span>♥ Like</span><span>💬 Comment</span><span>↗ Share</span>
            </div>
          </div>
        </div>

        {/* Right — meta */}
        <div className="w-full shrink-0 lg:w-[340px] space-y-4">
          <div className="rounded-2xl border bg-white p-4 dark:border-slate-800 dark:bg-slate-900 space-y-3">
            <h3 className="text-sm font-semibold">YouTube Main</h3>
            {error && <div className="rounded bg-red-50 px-2 py-1 text-xs text-red-600">{error}</div>}
            <label className="block text-xs font-medium">Series (select or type new)</label>
            <input list="series-list" value={seriesName} onChange={(e) => setSeriesName(e.target.value)} placeholder="e.g. NETCAT Mastery" className="w-full rounded border px-2 py-1.5 text-sm dark:bg-slate-800" />
            <datalist id="series-list">
              {seriesList.map((s) => <option key={s.id} value={s.name} />)}
            </datalist>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs font-medium">Episode #</label>
                <input type="number" value={episodeNumber} onChange={(e) => setEpisodeNumber(e.target.value === "" ? "" : Number(e.target.value))} placeholder="auto" className="w-full rounded border px-2 py-1.5 text-sm dark:bg-slate-800" />
              </div>
              <div>
                <label className="text-xs font-medium">Date</label>
                <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="w-full rounded border px-2 py-1.5 text-sm dark:bg-slate-800" />
              </div>
            </div>
            <label className="block text-xs font-medium">Title (Senario Lookup)</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Episode title" className="w-full rounded border px-2 py-1.5 text-sm dark:bg-slate-800" />
            <div className="grid grid-cols-2 gap-2">
              <label className="flex flex-col text-xs font-medium">Visibility
                <select value={visibility} onChange={(e) => setVisibility(e.target.value as any)} className="rounded border px-2 py-1.5 text-sm dark:bg-slate-800">
                  <option value="Private">Private</option>
                  <option value="Public">Public</option>
                </select>
              </label>
              <label className="flex flex-col text-xs font-medium">Collection
                <select value={collection} onChange={(e) => setCollection(e.target.value)} className="rounded border px-2 py-1.5 text-sm dark:bg-slate-800">
                  <option value="">— none —</option>
                  {collections.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
                </select>
              </label>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <label className="flex items-center gap-1"><input type="checkbox" checked={soundEffects} onChange={(e) => setSoundEffects(e.target.checked)} /> Sound FX</label>
              <label className="flex items-center gap-1"><input type="checkbox" checked={music} onChange={(e) => setMusic(e.target.checked)} /> Music</label>
              <label className="flex items-center gap-1">Subtitles <input type="number" value={subtitlesCount} min={0} onChange={(e) => setSubtitlesCount(Number(e.target.value))} className="w-12 rounded border px-1 py-0.5" /></label>
              <label className="flex items-center gap-1"><input type="checkbox" checked={thumbnailReady} onChange={(e) => setThumbnailReady(e.target.checked)} /> Thumbnail</label>
            </div>
            <div className="text-xs text-slate-500">Total duration: {scenes.reduce((s, c) => s + c.durationSec, 0)}s</div>
            <div className="flex gap-2">
              <button onClick={() => handleSave(false)} disabled={saving} className="flex-1 rounded-lg bg-slate-900 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-white dark:text-slate-900">{saving ? "Saving…" : "Save"}</button>
              <button onClick={() => handleSave(true)} disabled={saving} className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-slate-50">Queue render</button>
            </div>
            <a href="/emulator" className="block text-center text-xs text-slate-500 underline">Open in emulator →</a>
          </div>
        </div>
      </div>
    </>
  );
}
