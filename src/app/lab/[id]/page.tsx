"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { StudioNav } from "@/components/studio-nav";
import type { EpisodeScene, ContentRow } from "@/lib/types";
import { VISIBILITIES, type Visibility } from "@/lib/constants";

export default function LabEditPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [row, setRow] = useState<ContentRow | null>(null);
  const [scenes, setScenes] = useState<EpisodeScene[]>([]);
  const [selected, setSelected] = useState(0);
  const [title, setTitle] = useState("");
  const [visibility, setVisibility] = useState<Visibility>("Private");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const dash = await fetch("/api/dashboard", { credentials: "include" }).then((r) => r.json());
      const found = (dash.rows as ContentRow[]).find((r) => String(r.id) === id);
      if (!found) { setLoading(false); return; }
      setRow(found);
      setTitle(found.title);
      setVisibility(found.visibility);
      // load scenes
      const sc = await fetch(`/api/content/${id}/scenes`, { credentials: "include" }).then((r) => (r.ok ? r.json() : []));
      if (sc.length) setScenes(sc);
      else if (found.script) {
        setScenes([{ id: Date.now(), position: 0, durationSec: found.durationSec, command: found.script.command, tip: found.script.tip, audio: found.script.audio, notes: "" }]);
      }
      setLoading(false);
    }
    load();
  }, [id]);

  function updateScene(idx: number, patch: Partial<EpisodeScene>) {
    setScenes((prev) => prev.map((s, i) => (i === idx ? { ...s, ...patch } : s)));
  }
  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      // patch meta
      const metaRes = await fetch(`/api/content/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ title, visibility }) });
      if (!metaRes.ok) throw new Error((await metaRes.json()).error || "Save failed");
      // upsert scenes naive: delete all and recreate
      // fetch existing
      const existing: EpisodeScene[] = await fetch(`/api/content/${id}/scenes`, { credentials: "include" }).then((r) => r.json());
      for (const ex of existing) {
        await fetch(`/api/content/${id}/scenes/${ex.id}`, { method: "DELETE", credentials: "include" });
      }
      for (const sc of scenes) {
        await fetch(`/api/content/${id}/scenes`, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ command: sc.command, tip: sc.tip, audio: sc.audio, durationSec: sc.durationSec, notes: sc.notes }) });
      }
      router.refresh();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <><StudioNav /><div className="p-6 text-sm text-slate-500">Loading…</div></>;
  if (!row) return <><StudioNav /><div className="p-6 text-sm">Episode not found.</div></>;

  const current = scenes[selected];

  return (
    <>
      <StudioNav />
      <div className="mx-auto max-w-7xl p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold">Edit {row.episodeDisplay}</h1>
          <div className="flex gap-2">
            <a href={`/emulator/${id}`} className="rounded border px-3 py-1.5 text-xs">Open in emulator →</a>
            <button onClick={handleSave} disabled={saving} className="rounded bg-slate-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50">Save</button>
          </div>
        </div>
        {error && <div className="rounded bg-red-50 px-3 py-2 text-xs text-red-600">{error}</div>}
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Scenes</h3>
            {scenes.map((sc, idx) => (
              <div key={sc.id} onClick={() => setSelected(idx)} className={`cursor-pointer rounded border p-2 ${selected === idx ? "border-slate-900 bg-slate-50" : "bg-white"}`}>
                <div className="text-xs font-bold">SCN{idx + 1} · {sc.durationSec}s</div>
                <div className="truncate text-sm">{sc.command || "—"}</div>
              </div>
            ))}
            <button onClick={() => setScenes([...scenes, { id: Date.now(), position: scenes.length, durationSec: 15, command: "", tip: "", audio: true, notes: "" }])} className="w-full rounded border py-1 text-xs">+ Add scene</button>
            {current && (
              <div className="rounded border bg-white p-2 space-y-1">
                <input value={current.command} onChange={(e) => updateScene(selected, { command: e.target.value })} placeholder="command" className="w-full rounded border px-2 py-1 text-sm" />
                <input value={current.tip} onChange={(e) => updateScene(selected, { tip: e.target.value })} placeholder="tip" className="w-full rounded border px-2 py-1 text-sm" />
              </div>
            )}
          </div>
          <div className="flex justify-center">
            <div className="relative h-[640px] w-[360px] overflow-hidden rounded-[2rem] border-[10px] border-slate-900 bg-[#0b1020] flex items-center justify-center p-6 text-center">
              <div className="rounded bg-black/40 px-3 py-2">
                <div className="font-mono text-white">❯ {current?.command || "—"}</div>
                <div className="text-xs text-slate-300">{current?.tip}</div>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <label className="block text-xs font-medium">Title<input value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1 w-full rounded border px-2 py-1 text-sm" /></label>
            <label className="block text-xs font-medium">Visibility
              <select value={visibility} onChange={(e) => setVisibility(e.target.value as Visibility)} className="mt-1 w-full rounded border px-2 py-1 text-sm">{VISIBILITIES.map((s) => (<option key={s} value={s}>{s}</option>))}</select>
            </label>
          </div>
        </div>
      </div>
    </>
  );
}
