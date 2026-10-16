"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { StudioNav } from "@/components/studio-nav";
import { emptyLibrary, isLibraryData, libraryFromApi, LIBRARY_SECTIONS, newLibraryRecord, sceneCount } from "@/lib/library";
import type { LibraryColumn, LibraryData, LibraryRecord, LibrarySection, LibraryValue } from "@/lib/library";
import type { ContentRow } from "@/lib/types";

const control = "w-full min-w-32 rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-900";

export default function LibraryPage() {
  const router = useRouter();
  const [tab, setTab] = useState<LibrarySection>("main");
  const [data, setData] = useState<LibraryData>(emptyLibrary);
  const [storageKey, setStorageKey] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [episode, setEpisode] = useState("");
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const auth = await fetch("/api/auth/me", { credentials: "include" });
        if (auth.status === 401) { router.replace("/login"); return; }
        if (!auth.ok) throw new Error("Unable to verify your account. Please retry.");
        const user = await auth.json();
        if (!user.email) throw new Error("Unable to identify your account.");
        const key = `ytcm-library-v1:${user.email}`;
        const [dashboard, meta] = await Promise.all([
          fetch("/api/dashboard", { credentials: "include", cache: "no-store" }),
          fetch("/api/meta", { credentials: "include" }),
        ]);
        if (!dashboard.ok || !meta.ok) throw new Error("Unable to load Library data. Check your connection and retry.");
        const result: { rows: ContentRow[] } = await dashboard.json();
        const metadata: { collections: { name: string }[] } = await meta.json();
        const initial = libraryFromApi(result.rows, metadata.collections);
        let saved: LibraryData | null = null;
        let message = "";
        try {
          const stored = localStorage.getItem(key);
          if (stored) {
            const parsed: unknown = JSON.parse(stored);
            if (isLibraryData(parsed)) saved = parsed;
            else message = "Saved draft is incompatible. Loaded server data; export before making changes if needed.";
          }
        } catch { message = "Browser storage could not be read. Export your work to keep a copy."; }
        if (active) {
          setData(saved || initial);
          setStorageKey(key);
          setNotice(message || (saved ? "Restored your browser draft." : "Loaded existing episodes. Changes stay in this browser."));
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Unable to load Library.");
      } finally { if (active) setLoading(false); }
    }
    void load();
    return () => { active = false; };
  }, [router, revision]);

  function save(next: LibraryData) {
    setData(next);
    try {
      localStorage.setItem(storageKey, JSON.stringify(next));
      setNotice("Draft saved in this browser. Not synced to the server or YouTube.");
    } catch { setNotice("Could not save in browser storage. Export your draft now to avoid losing changes."); }
  }

  function update(id: string, field: string, value: LibraryValue) {
    save({ ...data, [tab]: data[tab].map((row) => row.id === id ? { ...row, [field]: value } : row) });
  }

  function remove(row: LibraryRecord) {
    const referenced = (tab === "episodes" || tab === "collections" || tab === "languages") && LIBRARY_SECTIONS.some((section) =>
      section.columns.some((column) => column.source === tab && data[section.key].some((item) => item[column.key] === row.id)));
    if (referenced) { setNotice("This record is used by another section. Clear its references before deleting it."); return; }
    if (window.confirm("Delete this row from your browser draft? Server data will not be deleted.")) {
      save({ ...data, [tab]: data[tab].filter((item) => item.id !== row.id) });
    }
  }

  function options(column: LibraryColumn): { value: string; label: string }[] {
    if (column.source) return data[column.source].map((row) => ({ value: row.id, label: String(row.name || row.id) }));
    return (column.options || []).map((value) => ({ value, label: value }));
  }

  function cell(row: LibraryRecord, column: LibraryColumn) {
    const label = `${column.label} for row ${row.id}`;
    const value = row[column.key] ?? "";
    if (column.key === "sceneCount") return <span className="font-medium">{sceneCount(data, tab === "episodes" ? row.id : String(row.episode))}</span>;
    if (column.readonly) return <span title={String(value)} className="block max-w-40 truncate font-mono text-xs text-slate-500">{value}</span>;
    if (column.kind === "bool") return <input aria-label={label} type="checkbox" checked={value === true} onChange={(e) => update(row.id, column.key, e.target.checked)} className="h-4 w-4 accent-blue-600" />;
    if (column.kind === "select") {
      const choices = options(column);
      return <select aria-label={label} className={control} value={String(value)} onChange={(e) => update(row.id, column.key, e.target.value)}>
        <option value="">Select…</option>
        {value !== "" && !choices.some((choice) => choice.value === String(value)) && <option value={String(value)}>{String(value)} (unavailable)</option>}
        {choices.map((choice) => <option key={choice.value} value={choice.value}>{choice.label}</option>)}
      </select>;
    }
    if (column.kind === "long") return <textarea aria-label={label} className={`${control} min-w-56`} rows={2} value={String(value)} onChange={(e) => update(row.id, column.key, e.target.value)} />;
    return <input aria-label={label} className={control} type={column.kind === "number" ? "number" : column.kind === "date" ? "date" : "text"}
      min={column.key === "subtitlesCount" ? 0 : 1} step={1} value={String(value)} onChange={(e) => {
        if (column.kind === "number") {
          if (e.target.value === "") { update(row.id, column.key, ""); return; }
          const number = Number(e.target.value);
          if (!Number.isInteger(number) || number < (column.key === "subtitlesCount" ? 0 : 1)) return;
          update(row.id, column.key, number);
        } else update(row.id, column.key, e.target.value);
      }} />;
  }

  const section = LIBRARY_SECTIONS.find((item) => item.key === tab)!;
  const filtered = data[tab].filter((row) => {
    if (tab === "main" && status && row.status !== status) return false;
    if (episode && row.episode !== episode) return false;
    return section.columns.some((column) => {
      const value = column.source ? options(column).find((choice) => choice.value === row[column.key])?.label : row[column.key];
      return String(value ?? "").toLowerCase().includes(query.toLowerCase());
    });
  });

  function exportDraft() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url; link.download = "youtube-library-draft.json"; link.click();
    URL.revokeObjectURL(url);
  }

  return <>
    <StudioNav />
    <main className="mx-auto max-w-7xl space-y-5 p-4 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div><p className="mb-1 text-xs font-semibold uppercase tracking-widest text-blue-600 dark:text-blue-400">YouTube content management</p>
          <h1 className="text-2xl font-semibold tracking-tight">Library</h1>
          <p className="mt-1 text-sm text-slate-500">Organize episodes, content, scenes, and production resources.</p></div>
        <Link href="/lab" className="rounded-lg border px-3 py-2 text-sm dark:border-slate-700">Open Lab →</Link>
      </div>
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-200">
        <strong>Frontend draft workspace.</strong> Edits are saved locally for this account and browser only. They do not update the backend or YouTube. Add episodes, collections, and languages to populate dropdowns.
      </div>
      <nav aria-label="Library sections" className="flex gap-1 overflow-x-auto border-b pb-2 dark:border-slate-800">
        {LIBRARY_SECTIONS.map((item) => <button key={item.key} aria-current={tab === item.key ? "page" : undefined} onClick={() => { setTab(item.key); setQuery(""); setStatus(""); setEpisode(""); }}
          className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium ${tab === item.key ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900" : "text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"}`}>
          {item.label} <span className="ml-1 text-xs opacity-60">{data[item.key].length}</span>
        </button>)}
      </nav>
      {loading ? <p role="status" className="py-10 text-center text-sm text-slate-500">Loading Library…</p> : error ?
        <div role="alert" className="rounded-xl border border-red-200 p-6 text-sm"><p>{error}</p><button className="mt-3 rounded-lg border px-3 py-2" onClick={() => setRevision((value) => value + 1)}>Retry</button></div> : <>
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="mr-auto text-lg font-semibold">{section.label}</h2>
            <button onClick={() => {
              if (!window.confirm("Discard all local Library edits and reload server data? Export a copy first if needed.")) return;
              try { localStorage.removeItem(storageKey); setRevision((value) => value + 1); }
              catch { setNotice("Could not clear browser storage. Your draft has not been discarded."); }
            }} className="rounded-lg border px-3 py-2 text-sm dark:border-slate-700">Reload server data</button>
            <button onClick={exportDraft} className="rounded-lg border px-3 py-2 text-sm dark:border-slate-700">Export draft</button>
            <button onClick={() => { save({ ...data, [tab]: [...data[tab], newLibraryRecord(tab, `draft-${crypto.randomUUID()}`)] }); setQuery(""); setStatus(""); setEpisode(""); }} className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700">+ Add row</button>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input aria-label={`Search ${section.label}`} placeholder={`Search ${section.label.toLowerCase()}…`} value={query} onChange={(e) => setQuery(e.target.value)} className={`${control} max-w-xs`} />
            {tab === "main" && <select aria-label="Filter by status" className={`${control} max-w-44`} value={status} onChange={(e) => setStatus(e.target.value)}><option value="">All statuses</option>{LIBRARY_SECTIONS[0].columns.find((c) => c.key === "status")!.options!.map((value) => <option key={value}>{value}</option>)}</select>}
            {section.columns.some((column) => column.key === "episode") && <select aria-label="Filter by episode" className={`${control} max-w-52`} value={episode} onChange={(e) => setEpisode(e.target.value)}><option value="">All episodes</option>{data.episodes.map((row) => <option key={row.id} value={row.id}>{row.name || row.id}</option>)}</select>}
            <span className="ml-auto text-xs text-slate-500">{filtered.length} of {data[tab].length} rows</span>
          </div>
          <div className="thin-scroll overflow-x-auto rounded-xl border bg-white dark:border-slate-800 dark:bg-slate-900" role="region" aria-label={`${section.label} table`} tabIndex={0}>
            <table className="min-w-full text-left text-sm">
              <caption className="sr-only">{section.label} — editable browser draft</caption>
              <thead className="bg-slate-50 text-xs text-slate-500 dark:bg-slate-800"><tr>{section.columns.map((column) => <th scope="col" key={column.key} className="whitespace-nowrap px-3 py-3 font-medium">{column.label}</th>)}<th scope="col" className="px-3 py-3">Actions</th></tr></thead>
              <tbody>{filtered.map((row) => <tr key={row.id} className="border-t border-slate-100 align-top dark:border-slate-800">{section.columns.map((column) => <td key={column.key} className="px-3 py-3">{cell(row, column)}</td>)}<td className="px-3 py-3"><div className="flex items-center gap-2">{(tab === "main" || tab === "episodes") && /^\d+$/.test(row.id) && <><Link href={`/lab/${row.id}`} className="text-xs text-blue-600 dark:text-blue-400">Lab</Link><Link href={`/emulator/${row.id}`} className="text-xs text-blue-600 dark:text-blue-400">Emulator</Link>{tab === "main" && <a href={`/api/content/${row.id}/video`} target="_blank" rel="noreferrer" className="text-xs text-blue-600 dark:text-blue-400">Video</a>}</>}<button aria-label={`Delete row ${row.id}`} onClick={() => remove(row)} className="rounded px-2 py-1.5 text-xs text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950">Delete</button></div></td></tr>)}</tbody>
            </table>
            {filtered.length === 0 && <div className="px-6 py-12 text-center"><p className="font-medium">{data[tab].length ? "No matching rows" : `No ${section.label.toLowerCase()} yet`}</p><p className="mt-1 text-sm text-slate-500">{data[tab].length ? "Try a different search or filter." : "Add a row to start organizing this section."}</p></div>}
          </div>
          <p role="status" aria-live="polite" className="text-xs text-slate-500">{notice}</p>
        </>}
    </main>
  </>;
}
