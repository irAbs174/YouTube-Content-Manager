import { describe, expect, it } from "vitest";
import {
  PLACE_KEYS,
  PLACE_TABS,
  cellPayload,
  displayCell,
  filterableColumns,
  filterRows,
  isBlank,
  isPlaceKey,
  matchesFilter,
  optionLabel,
  searchRows,
} from "@/lib/library";
import type { PlaceColumn, PlaceOptions } from "@/lib/library-types";

const options: PlaceOptions = {
  episodes: [{ id: 1, label: "Seed Series #1" }],
  collections: [{ id: 3, label: "OSINT" }],
  languages: [{ id: 2, label: "English" }],
  statuses: ["Public", "Schedule", "Private", "Draft", "Not List"],
  assetTypes: ["Emojie", "Fonts"],
  collectionTypes: ["course", "Play List"],
};

const column = (over: Partial<PlaceColumn> = {}): PlaceColumn => ({
  key: "title",
  label: "Title",
  type: "text",
  source: null,
  editable: true,
  ...over,
});

describe("place keys", () => {
  it("covers every workbook sheet place", () => {
    expect(PLACE_KEYS).toEqual([
      "main",
      "contents",
      "scenes",
      "episodes",
      "collections",
      "languages",
      "assets",
      "subtitles",
    ]);
  });

  it("labels every place", () => {
    for (const key of PLACE_KEYS) {
      expect(PLACE_TABS[key]).toBeTruthy();
      expect(isPlaceKey(key)).toBe(true);
    }
    expect(isPlaceKey("nope")).toBe(false);
  });
});

describe("optionLabel", () => {
  it("resolves id-based selects to their label", () => {
    expect(optionLabel(options, "collections", 3)).toBe("OSINT");
    expect(optionLabel(options, "episodes", 1)).toBe("Seed Series #1");
  });

  it("returns plain strings for list selects", () => {
    expect(optionLabel(options, "statuses", "Draft")).toBe("Draft");
    expect(optionLabel(options, "assetTypes", "Fonts")).toBe("Fonts");
  });

  it("falls back to an empty label for unknown ids", () => {
    expect(optionLabel(options, "collections", 999)).toBe("");
  });
});

describe("isBlank", () => {
  it("treats null, undefined and empty strings as blank", () => {
    expect(isBlank(null)).toBe(true);
    expect(isBlank(undefined)).toBe(true);
    expect(isBlank("  ")).toBe(true);
    expect(isBlank("x")).toBe(false);
    expect(isBlank(0)).toBe(false);
    expect(isBlank(false)).toBe(false);
  });
});

describe("matchesFilter", () => {
  it("passes everything for All", () => {
    expect(matchesFilter("Public", "All")).toBe(true);
    expect(matchesFilter("Public", "")).toBe(true);
  });

  it("compares loosely typed values as strings", () => {
    expect(matchesFilter("Public", "Public")).toBe(true);
    expect(matchesFilter(true, "true")).toBe(true);
    expect(matchesFilter(3, "3")).toBe(true);
    expect(matchesFilter(3, "4")).toBe(false);
  });

  it("rejects blank cells when a filter is active", () => {
    expect(matchesFilter("", "Public")).toBe(false);
    expect(matchesFilter(null, "Public")).toBe(false);
  });
});

describe("filterRows", () => {
  const rows = [
    { id: 1, status: "Public", collectionId: 3 },
    { id: 2, status: "Draft", collectionId: 1 },
  ];

  it("returns every row when no filter is active", () => {
    expect(filterRows(rows, {})).toHaveLength(2);
    expect(filterRows(rows, { status: "All" })).toHaveLength(2);
  });

  it("applies every active filter", () => {
    expect(filterRows(rows, { status: "Public" })).toHaveLength(1);
    expect(filterRows(rows, { status: "Public", collectionId: "1" })).toHaveLength(0);
  });
});

describe("searchRows", () => {
  const rows = [
    { id: 1, title: "nmap -sC explained" },
    { id: 2, title: "netcat listener" },
  ];

  it("matches case-insensitively across cells", () => {
    expect(searchRows(rows, "NMAP")).toHaveLength(1);
    expect(searchRows(rows, "netcat")).toHaveLength(1);
    expect(searchRows(rows, "")).toHaveLength(2);
  });
});

describe("displayCell", () => {
  const row = { id: 1, collectionId: 3, music: true, title: "hello" };

  it("renders select cells with their label", () => {
    expect(
      displayCell(row, column({ key: "collectionId", type: "select", source: "collections" }), options),
    ).toBe("OSINT");
  });

  it("renders booleans as a check mark", () => {
    expect(displayCell(row, column({ key: "music", type: "bool" }), options)).toBe("✓");
    expect(
      displayCell({ id: 2, music: false }, column({ key: "music", type: "bool" }), options),
    ).toBe("—");
  });

  it("renders blank cells as an em dash", () => {
    expect(displayCell({ id: 3, title: "" }, column(), options)).toBe("—");
  });
});

describe("cellPayload", () => {
  it("sends booleans as booleans", () => {
    expect(cellPayload(column({ key: "music", type: "bool" }), "")).toEqual({ music: false });
    expect(cellPayload(column({ key: "music", type: "bool" }), true)).toEqual({ music: true });
  });

  it("sends select ids as numbers and statuses as strings", () => {
    expect(
      cellPayload(column({ key: "collectionId", type: "select", source: "collections" }), "3"),
    ).toEqual({ collectionId: 3 });
    expect(
      cellPayload(column({ key: "status", type: "select", source: "statuses" }), "Draft"),
    ).toEqual({ status: "Draft" });
  });

  it("clears a select with an empty value", () => {
    expect(
      cellPayload(column({ key: "collectionId", type: "select", source: "collections" }), ""),
    ).toEqual({ collectionId: null });
  });

  it("sends numbers as numbers and text as strings", () => {
    expect(cellPayload(column({ key: "episodeNumber", type: "number" }), "12")).toEqual({
      episodeNumber: 12,
    });
    expect(cellPayload(column(), "new title")).toEqual({ title: "new title" });
  });
});

describe("filterableColumns", () => {
  it("only offers select columns as filters", () => {
    const columns = [
      column({ key: "title", type: "text" }),
      column({ key: "status", type: "select", source: "statuses" }),
      column({ key: "subtitlesCount", type: "count" }),
    ];
    expect(filterableColumns(columns).map((c) => c.key)).toEqual(["status"]);
  });
});
