"use client";

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { COLLECTIONS, EFFECT_OPTIONS, STATUSES, SUBTITLE_OPTIONS } from "@/lib/constants";
import { addDays, todayISO } from "@/lib/dates";
import { inputClass, primaryButtonClass, ghostButtonClass } from "./ui";

interface AddEpisodeDialogProps {
  onClose: () => void;
  onCreated: () => void;
}

const SOUND_SUGGESTIONS = COLLECTIONS.flatMap((c) => c.sounds);

export function AddEpisodeDialog({ onClose, onCreated }: AddEpisodeDialogProps) {
  const [form, setForm] = useState({
    title: "",
    date: todayISO(),
    status: "Draft",
    collection: COLLECTIONS[0].name,
    soundMusic: "",
    effects: "",
    subtitles: "EN",
    thumbnail: "",
    durationSec: 45,
    render: true,
    command: "",
    tip: "",
    audio: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, [onClose]);

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, durationSec: Number(form.durationSec) }),
      });
      const json = (await res.json().catch(() => ({}))) as { error?: string };
      if (!res.ok) throw new Error(json.error ?? "Could not create episode");
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create episode");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/60 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-episode-title"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <form
        onSubmit={submit}
        className="dashboard-fade-in max-h-[92vh] w-full overflow-y-auto rounded-t-2xl border border-slate-200 bg-white p-5 shadow-2xl sm:max-w-2xl sm:rounded-2xl sm:p-6 dark:border-slate-800 dark:bg-slate-900"
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <h2 id="add-episode-title" className="text-lg font-semibold tracking-tight">
              New episode
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Add a Short to the master table. Metrics start at zero and build as it publishes.
            </p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close" className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200">
            ✕
          </button>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Title" className="sm:col-span-2">
            <input
              required
              minLength={3}
              maxLength={140}
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
              placeholder="e.g. NETCAT #21 · Extra Verbose(-vv)"
              className={inputClass}
            />
          </Field>

          <Field label="Date">
            <input
              required
              type="date"
              value={form.date}
              max={addDays(todayISO(), 365)}
              onChange={(e) => set("date", e.target.value)}
              className={inputClass}
            />
          </Field>

          <Field label="Status">
            <select value={form.status} onChange={(e) => set("status", e.target.value)} className={inputClass}>
              {STATUSES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </Field>

          <Field label="Collection">
            <select value={form.collection} onChange={(e) => set("collection", e.target.value)} className={inputClass}>
              {COLLECTIONS.map((c) => (
                <option key={c.name}>{c.name}</option>
              ))}
            </select>
          </Field>

          <Field label="Duration (seconds)">
            <input
              type="number"
              min={5}
              max={180}
              value={form.durationSec}
              onChange={(e) => set("durationSec", Number(e.target.value))}
              className={inputClass}
            />
          </Field>

          <Field label="Sound / Music">
            <input
              list="sound-suggestions"
              value={form.soundMusic}
              onChange={(e) => set("soundMusic", e.target.value)}
              placeholder="Royalty-free library"
              className={inputClass}
            />
            <datalist id="sound-suggestions">
              {SOUND_SUGGESTIONS.map((s) => (
                <option key={s} value={s} />
              ))}
            </datalist>
          </Field>

          <Field label="Effects">
            <input
              list="effect-suggestions"
              value={form.effects}
              onChange={(e) => set("effects", e.target.value)}
              placeholder="Glitch strips · Neon glow"
              className={inputClass}
            />
            <datalist id="effect-suggestions">
              {EFFECT_OPTIONS.map((s) => (
                <option key={s} value={s} />
              ))}
            </datalist>
          </Field>

          <Field label="Subtitles">
            <select value={form.subtitles} onChange={(e) => set("subtitles", e.target.value)} className={inputClass}>
              {SUBTITLE_OPTIONS.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </Field>

          <Field label="Thumbnail path">
            <input
              value={form.thumbnail}
              onChange={(e) => set("thumbnail", e.target.value)}
              placeholder="thumbs/netcat/ep-21.jpg"
              className={inputClass}
            />
          </Field>
        </div>

        <fieldset className="mt-5 space-y-4 rounded-xl border border-slate-200 p-4 dark:border-slate-700">
          <legend className="px-1 text-xs font-semibold text-slate-600 dark:text-slate-300">FFmpeg render</legend>

          <label className="flex items-center gap-2.5 text-sm font-medium">
            <input
              type="checkbox"
              checked={form.render}
              onChange={(e) => set("render", e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
            Render a 1080×1920 Short video with FFmpeg
          </label>

          {form.render && (
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="On-screen command" className="sm:col-span-2">
                <input
                  required
                  value={form.command}
                  onChange={(e) => set("command", e.target.value)}
                  placeholder="nc -lv 9999"
                  className={`${inputClass} font-mono`}
                />
              </Field>
              <Field label="Tip card" className="sm:col-span-2">
                <input
                  value={form.tip}
                  onChange={(e) => set("tip", e.target.value)}
                  placeholder="Verbose listener confirms the peer."
                  className={inputClass}
                />
              </Field>
              <label className="flex items-center gap-2.5 text-sm sm:col-span-2">
                <input
                  type="checkbox"
                  checked={form.audio}
                  onChange={(e) => set("audio", e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                Generated audio track (key clicks + low drone)
              </label>
            </div>
          )}
        </fieldset>

        {error && (
          <p role="alert" className="mt-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
            {error}
          </p>
        )}

        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" onClick={onClose} className={ghostButtonClass}>
            Cancel
          </button>
          <button type="submit" disabled={submitting} className={primaryButtonClass}>
            {submitting ? "Saving…" : "Create episode"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, children, className = "" }: { label: string; children: ReactNode; className?: string }) {
  return (
    <label className={`flex flex-col gap-1.5 ${className}`}>
      <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">{label}</span>
      {children}
    </label>
  );
}
