/**
 * Pure helpers for the Library "spec places".
 *
 * Everything here is framework-free so it can be unit-tested with vitest and
 * reused by the table renderer, the filter bar and the row editors.
 */

import type { LibraryRow, PlaceColumn, PlaceKey, PlaceOptions } from "./library-types";

/** The places, in the order the Library shows them. */
export const PLACE_KEYS: PlaceKey[] = [
  "main",
  "contents",
  "scenes",
  "episodes",
  "collections",
  "languages",
  "assets",
  "subtitles",
];

/** Short labels for the tab bar. */
export const PLACE_TABS: Record<PlaceKey, string> = {
  main: "Main Library",
  contents: "Contents",
  scenes: "Scenes",
  episodes: "Episodes",
  collections: "Collections",
  languages: "Languages",
  assets: "Assets",
  subtitles: "Subtitle",
};

export function isPlaceKey(value: string): value is PlaceKey {
  return (PLACE_KEYS as string[]).includes(value);
}

/** Human label for a select-list value. */
export function optionLabel(
  options: PlaceOptions,
  source: string | null,
  value: unknown,
): string {
  if (source === null) return String(value ?? "");
  if (source === "statuses" || source === "assetTypes" || source === "collectionTypes") {
    return String(value ?? "");
  }
  const list = (options as unknown as Record<string, SelectOptionLike[]>)[source] ?? [];
  const found = list.find((item) => String(item.id) === String(value));
  return found ? found.label : "";
}

interface SelectOptionLike {
  id: number;
  label: string;
}

/** True for `null`, `undefined` and blank strings. */
export function isBlank(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === "string") return value.trim() === "";
  return false;
}

/** Does a cell pass a single filter?  "All" (or a blank filter) always passes. */
export function matchesFilter(value: unknown, filter: string | undefined): boolean {
  if (!filter || filter === "All") return true;
  if (isBlank(value)) return false;
  if (typeof value === "boolean") return String(value) === filter;
  return String(value) === filter;
}

/** Filter rows by a map of column key → filter value. */
export function filterRows<T extends LibraryRow>(
  rows: T[],
  filters: Record<string, string>,
): T[] {
  const active = Object.entries(filters).filter(([, value]) => value && value !== "All");
  if (active.length === 0) return rows;
  return rows.filter((row) =>
    active.every(([key, value]) => matchesFilter(row[key], value)),
  );
}

/** Free-text search across every cell of a row. */
export function searchRows<T extends LibraryRow>(rows: T[], term: string): T[] {
  const needle = term.trim().toLowerCase();
  if (!needle) return rows;
  return rows.filter((row) =>
    Object.values(row).some((value) => String(value ?? "").toLowerCase().includes(needle)),
  );
}

/** The text shown in a cell when the cell is not editable. */
export function displayCell(
  row: LibraryRow,
  column: PlaceColumn,
  options: PlaceOptions,
): string {
  const value = row[column.key];
  if (column.type === "select") {
    if (isBlank(value)) return "—";
    return optionLabel(options, column.source, value);
  }
  if (column.type === "bool") {
    return value ? "✓" : "—";
  }
  if (isBlank(value)) return "—";
  return String(value);
}

/** The payload the API expects for an edited cell. */
export function cellPayload(
  column: PlaceColumn,
  value: string | number | boolean | null,
): Record<string, unknown> {
  if (column.type === "bool") {
    return { [column.key]: Boolean(value) };
  }
  if (column.type === "number" || column.type === "count") {
    const parsed = Number(value);
    return { [column.key]: Number.isFinite(parsed) ? parsed : 0 };
  }
  if (column.type === "select") {
    if (value === null || value === "") return { [column.key]: null };
    const parsed = Number(value);
    // Language / collection / episode selects carry numeric ids; status-like
    // selects carry plain strings.
    return { [column.key]: Number.isFinite(parsed) && String(parsed) === String(value) ? parsed : value };
  }
  return { [column.key]: value === null ? "" : String(value) };
}

/** Columns that make sense as a filter for a place. */
export function filterableColumns(columns: PlaceColumn[]): PlaceColumn[] {
  return columns.filter((column) => column.type === "select");
}
