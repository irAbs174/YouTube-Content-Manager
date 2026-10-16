import { describe, expect, it } from "vitest";
import { emptyLibrary, isLibraryData, libraryFromApi, LIBRARY_SECTIONS, LIBRARY_STATUSES, newLibraryRecord, sceneCount } from "../library";
import type { ContentRow } from "../types";

describe("Library sections", () => {
  it("provides all eight requested tables and status choices", () => {
    expect(LIBRARY_SECTIONS.map((section) => section.label)).toEqual([
      "Main library", "Contents", "Scenes", "Episodes", "Collections", "Languages", "Assets", "Subtitle",
    ]);
    expect(LIBRARY_STATUSES).toEqual(["Public", "Schedule", "Private", "Draft", "Not List"]);
    expect(LIBRARY_SECTIONS.map((section) => section.columns.length)).toEqual([9, 11, 8, 5, 6, 2, 6, 4]);
  });

  it("creates defaults with booleans and non-negative subtitle counts", () => {
    const row = newLibraryRecord("main", "test");
    expect(row).toMatchObject({ id: "test", status: "Draft", soundEffects: false, music: false, thumbnail: false, subtitlesCount: 0 });
    expect(newLibraryRecord("scenes", "scene")).toMatchObject({ sceneNumber: 1, episode: "" });
    expect(newLibraryRecord("languages", "language")).toEqual({ id: "language", name: "" });
  });
});

describe("API adapter", () => {
  it("preserves episode relations, deduplicates collections, and includes scenes beyond the old 20-row limit", () => {
    const rows = Array.from({ length: 25 }, (_, index) => ({
      id: index + 1, episodeNumber: index + 1, episodeDisplay: `Series #${index + 1}`, title: "Title",
      date: "2026-10-16", status: "Private", visibility: "Private", collection: "Tutorials",
      soundEffects: true, music: false, subtitlesCount: 2, thumbnailReady: true,
      scenes: [{ id: index + 100, position: 0, durationSec: 10, command: "Scenario", tip: "Hook", notes: "Body", audio: true }],
    })) as ContentRow[];
    const data = libraryFromApi(rows, [{ name: "Tutorials" }, { name: "Tutorials" }]);
    expect(data.collections).toHaveLength(1);
    expect(data.main).toHaveLength(25);
    expect(data.scenes).toHaveLength(25);
    expect(data.main[0]).toMatchObject({ episode: "1", collection: data.collections[0].id, subtitlesCount: 2 });
    expect(data.scenes[24]).toMatchObject({ episode: "25", sceneNumber: 1, hook: "Hook", scenario: "Scenario", body: "Body" });
    expect(data.contents).toEqual([]); // no fabricated metadata
    expect(sceneCount(data, "25")).toBe(1);
    data.scenes.push({ id: "local", episode: "25" });
    expect(sceneCount(data, "25")).toBe(2);
    expect(sceneCount(data, "missing")).toBe(0);
    expect(isLibraryData(data)).toBe(true);
  });
});

describe("browser draft validation", () => {
  it("accepts serializable records and rejects corrupt storage", () => {
    expect(isLibraryData(emptyLibrary())).toBe(true);
    expect(isLibraryData(null)).toBe(false);
    expect(isLibraryData({ main: [] })).toBe(false);
    expect(isLibraryData({ ...emptyLibrary(), main: [null] })).toBe(false);
    expect(isLibraryData({ ...emptyLibrary(), main: [{ id: 1 }] })).toBe(false);
    expect(isLibraryData({ ...emptyLibrary(), main: [{ id: "1", nested: {} }] })).toBe(false);
  });
});
