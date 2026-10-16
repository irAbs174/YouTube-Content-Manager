import type { ContentRow } from "./types";

export const LIBRARY_STATUSES = ["Public", "Schedule", "Private", "Draft", "Not List"];
export type LibrarySection = "main" | "contents" | "scenes" | "episodes" | "collections" | "languages" | "assets" | "subtitle";
export type LibraryValue = string | number | boolean;
export type LibraryRecord = { id: string } & Record<string, LibraryValue>;
export type LibraryData = Record<LibrarySection, LibraryRecord[]>;
type FieldKind = "text" | "long" | "number" | "date" | "bool" | "select";
export interface LibraryColumn { key: string; label: string; kind?: FieldKind; source?: "episodes" | "collections" | "languages"; options?: string[]; readonly?: boolean }
export const LIBRARY_SECTIONS: { key: LibrarySection; label: string; columns: LibraryColumn[] }[] = [
  { key: "main", label: "Main library", columns: [
    { key: "episode", label: "Episode", kind: "select", source: "episodes" },
    { key: "date", label: "Date", kind: "date" }, { key: "title", label: "Title" },
    { key: "status", label: "Status", kind: "select", options: LIBRARY_STATUSES },
    { key: "collection", label: "Collection", kind: "select", source: "collections" },
    { key: "soundEffects", label: "Sound Effects", kind: "bool" }, { key: "music", label: "Music", kind: "bool" },
    { key: "subtitlesCount", label: "Subtitles", kind: "number" }, { key: "thumbnail", label: "Thumbnail", kind: "bool" },
  ] },
  { key: "contents", label: "Contents", columns: [
    { key: "id", label: "ID", readonly: true }, { key: "episode", label: "Episode", kind: "select", source: "episodes" },
    { key: "language", label: "Language", kind: "select", source: "languages" }, { key: "title", label: "Title" },
    { key: "description", label: "Description", kind: "long" }, { key: "tags", label: "Tags" }, { key: "subtitles", label: "Subtitles", kind: "long" },
    { key: "relatedVideo", label: "Related Video", kind: "select", source: "episodes" }, { key: "pinnedComment", label: "Pinned Comment", kind: "long" },
    { key: "music", label: "Music" }, { key: "thumbnail", label: "Thumbnail" },
  ] },
  { key: "scenes", label: "Scenes", columns: [
    { key: "id", label: "ID", readonly: true }, { key: "episode", label: "Episode", kind: "select", source: "episodes" },
    { key: "sceneCount", label: "SCN Count", readonly: true }, { key: "sceneNumber", label: "SCN Number", kind: "number" },
    { key: "title", label: "Scene Title" }, { key: "hook", label: "SCN Hook", kind: "long" },
    { key: "scenario", label: "SCN Scenario", kind: "long" }, { key: "body", label: "SCN Body", kind: "long" },
  ] },
  { key: "episodes", label: "Episodes", columns: [
    { key: "episodeNumber", label: "Episode number", kind: "number" }, { key: "collection", label: "Collection", kind: "select", source: "collections" },
    { key: "name", label: "Episode" }, { key: "sharedLink", label: "Shared Link" }, { key: "sceneCount", label: "SCN Count", readonly: true },
  ] },
  { key: "collections", label: "Collections", columns: [
    { key: "id", label: "ID", readonly: true }, { key: "name", label: "Name" }, { key: "title", label: "Title" },
    { key: "description", label: "Description", kind: "long" }, { key: "type", label: "Type" }, { key: "shareLink", label: "Share Link" },
  ] },
  { key: "languages", label: "Languages", columns: [{ key: "id", label: "ID", readonly: true }, { key: "name", label: "Name" }] },
  { key: "assets", label: "Assets", columns: [
    { key: "id", label: "Assets ID", readonly: true }, { key: "type", label: "Type", kind: "select", options: ["Fonts", "img", "Audio", "Video", "Music", "Sound Effects", "Other"] },
    { key: "name", label: "Name" }, { key: "context", label: "Context" }, { key: "description", label: "Description", kind: "long" }, { key: "storageLocation", label: "Storage Location" },
  ] },
  { key: "subtitle", label: "Subtitle", columns: [
    { key: "episode", label: "Episode", kind: "select", source: "episodes" }, { key: "language", label: "Language", kind: "select", source: "languages" },
    { key: "duration", label: "Time duration" }, { key: "text", label: "Text", kind: "long" },
  ] },
];

export function emptyLibrary(): LibraryData {
  return { main: [], contents: [], scenes: [], episodes: [], collections: [], languages: [], assets: [], subtitle: [] };
}

/** Adapt only fields that exist in the current API; do not invent metadata. */
export function libraryFromApi(rows: ContentRow[], collections: { name: string }[]): LibraryData {
  const data = emptyLibrary();
  const names = [...new Set([...collections.map((c) => c.name), ...rows.map((r) => r.collection)].filter(Boolean))];
  data.collections = names.map((name, i) => ({ id: `collection-${i + 1}`, name, title: "", description: "", type: "", shareLink: "" }));
  for (const row of rows) {
    const episode = String(row.id);
    const collection = data.collections.find((c) => c.name === row.collection)?.id || "";
    data.episodes.push({ id: episode, episodeNumber: row.episodeNumber, name: row.episodeDisplay, collection, sharedLink: "" });
    data.main.push({ id: episode, episode, date: row.date, title: row.title, status: row.status || row.visibility, collection,
      soundEffects: row.soundEffects, music: row.music, subtitlesCount: row.subtitlesCount, thumbnail: row.thumbnailReady });
    for (const scene of row.scenes || []) {
      data.scenes.push({ id: String(scene.id), episode, sceneNumber: scene.position + 1, title: "", hook: scene.tip, scenario: scene.command, body: scene.notes });
    }
  }
  return data;
}

export function sceneCount(data: LibraryData, episodeId: string): number {
  return data.scenes.filter((scene) => scene.episode === episodeId).length;
}

export function newLibraryRecord(section: LibrarySection, id: string): LibraryRecord {
  const record: LibraryRecord = { id };
  for (const column of LIBRARY_SECTIONS.find((s) => s.key === section)!.columns) {
    if (column.key === "id" || column.readonly) continue;
    record[column.key] = column.kind === "bool" ? false : column.kind === "number" ? (column.key === "subtitlesCount" ? 0 : 1) : "";
  }
  if (section === "main") record.status = "Draft";
  return record;
}

/** Reject malformed or incompatible browser storage instead of crashing the page. */
export function isLibraryData(value: unknown): value is LibraryData {
  if (!value || typeof value !== "object") return false;
  return LIBRARY_SECTIONS.every(({ key }) => {
    const rows = (value as Record<string, unknown>)[key];
    return Array.isArray(rows) && rows.every((row: unknown) => row !== null && typeof row === "object" &&
      typeof (row as LibraryRecord).id === "string" && Object.values(row).every((v) => ["string", "number", "boolean"].includes(typeof v)));
  });
}
