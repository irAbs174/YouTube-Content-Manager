"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { StudioNav } from "@/components/studio-nav";
import { PlaceTable } from "@/components/library/place-table";
import {
  PLACE_KEYS,
  PLACE_TABS,
  filterableColumns,
  filterRows,
  isPlaceKey,
  searchRows,
} from "@/lib/library";
import type {
  LibraryRow,
  PlaceKey,
  PlaceOptions,
  PlaceSpec,
  PlacesPayload,
} from "@/lib/library-types";

const EMPTY_OPTIONS: PlaceOptions = {
  episodes: [],
  collections: [],
  languages: [],
  statuses: [],
  assetTypes: [],
  collectionTypes: [],
};

export default function LibraryPage() {
  const [tab, setTab] = useState<PlaceKey>("main");
  const [specs, setSpecs] = useState<PlaceSpec[]>([]);
  const [options, setOptions] = useState<PlaceOptions>(EMPTY_OPTIONS);
  const [rows, setRows] = useState<LibraryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyRowId, setBusyRowId] = useState<number | null>(null);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [search, setSearch] = useState("");

  // Load the place spec (columns + select options) once.
  useEffect(() => {
    fetch("/api/library/places", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((payload: PlacesPayload | null) => {
        if (!payload) return;
        setSpecs(payload.places ?? []);
        setOptions(payload.options ?? EMPTY_OPTIONS);
      })
      .catch(() => setError("Could not load the Library spec."));
  }, []);

  // Load the rows of the active place.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`/api/library/${tab}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((data: LibraryRow[]) => {
        if (!cancelled) setRows(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        if (!cancelled) setRows([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [tab]);

  const place = useMemo(
    () => specs.find((spec) => spec.key === tab) ?? null,
    [specs, tab],
  );

  const visibleRows = useMemo(() => {
    const byFilter = filterRows(rows, filters);
    return searchRows(byFilter, search);
  }, [rows, filters, search]);

  const filterColumns = useMemo(
    () => (place ? filterableColumns(place.columns) : []),
    [place],
  );

  const handlePatch = useCallback(
    async (rowId: number, payload: Record<string, unknown>) => {
      setBusyRowId(rowId);
      setError(null);
      try {
        const response = await fetch(`/api/library/${tab}/${rowId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(payload),
        });
        const body = await response.json().catch(() => null);
        if (!response.ok) {
          setError(body?.error ?? "Could not save the change.");
          return;
        }
        // Swap the patched row in place so the table stays responsive.
        setRows((current) =>
          current.map((row) => (row.id === rowId ? { ...row, ...body } : row)),
        );
      } catch {
        setError("Network error while saving.");
      } finally {
        setBusyRowId(null);
      }
    },
    [tab],
  );

  function selectTab(next: string) {
    if (!isPlaceKey(next)) return;
    setTab(next);
    setFilters({});
    setSearch("");
  }

  return (
    <>
      <StudioNav />
      <main className="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="text-xl font-semibold">Library</h1>
            <p className="text-xs text-slate-500">
              {place ? (
                <>
                  {place.title} — <span className="text-slate-400">{place.sheet}</span>
                </>
              ) : (
                "Every sheet of the YouTube Master workbook."
              )}
            </p>
          </div>
          <div className="flex flex-wrap gap-1 rounded-full bg-slate-100 p-1 dark:bg-slate-800">
            {PLACE_KEYS.map((key) => (
              <button
                key={key}
                onClick={() => selectTab(key)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                  tab === key
                    ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
                    : "text-slate-600 hover:bg-white/60 dark:text-slate-400 dark:hover:bg-slate-700/60"
                }`}
              >
                {PLACE_TABS[key]}
              </button>
            ))}
          </div>
        </div>

        {place?.description && (
          <p className="rounded-lg border border-dashed px-3 py-2 text-xs text-slate-500 dark:border-slate-800">
            {place.description}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-2 text-xs">
          {filterColumns.map((column) => (
            <label key={column.key} className="flex items-center gap-1">
              <span className="text-slate-500">{column.label}</span>
              <select
                aria-label={`Filter by ${column.label}`}
                value={filters[column.key] ?? "All"}
                onChange={(event) =>
                  setFilters((current) => ({
                    ...current,
                    [column.key]: event.target.value,
                  }))
                }
                className="cursor-pointer rounded border border-slate-200 bg-white px-2 py-1 outline-none focus:ring-2 focus:ring-slate-400 dark:border-slate-700 dark:bg-slate-900"
              >
                <option value="All">All</option>
                {column.source === "statuses" &&
                  options.statuses.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                {column.source === "collections" &&
                  options.collections.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                {column.source === "languages" &&
                  options.languages.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                {column.source === "episodes" &&
                  options.episodes.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
              </select>
            </label>
          ))}
          <input
            type="search"
            value={search}
            placeholder="Search…"
            aria-label="Search rows"
            onChange={(event) => setSearch(event.target.value)}
            className="rounded border border-slate-200 bg-white px-2 py-1 outline-none focus:ring-2 focus:ring-slate-400 dark:border-slate-700 dark:bg-slate-900"
          />
          <span className="ml-auto text-slate-500">
            {visibleRows.length} of {rows.length} rows
          </span>
        </div>

        {error && (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-300">
            {error}
          </div>
        )}

        {loading ? (
          <div className="rounded-xl border border-dashed p-8 text-center text-sm text-slate-500">
            Loading {place?.title ?? "rows"}…
          </div>
        ) : place ? (
          <PlaceTable
            columns={place.columns}
            rows={visibleRows}
            options={options}
            onPatch={handlePatch}
            busyRowId={busyRowId}
            emptyMessage={`No rows in ${place.title} yet.`}
          />
        ) : null}
      </main>
    </>
  );
}
