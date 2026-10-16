import { describe, expect, it } from "vitest";
import { addDays, formatDateLong } from "../dates";
import { fmtDuration, fmtPct, pad2, shorten } from "../format";
import { bucketSeries } from "../series";
import type { SeriesPoint } from "../types";

describe("date helpers", () => {
  it("adds days across month and leap-year boundaries", () => {
    expect(addDays("2024-02-28", 1)).toBe("2024-02-29");
    expect(addDays("2024-02-29", 1)).toBe("2024-03-01");
  });

  it("formats dates consistently in UTC", () => {
    expect(formatDateLong("2026-10-15")).toBe("Oct 15, 2026");
  });
});

describe("format helpers", () => {
  it("formats durations, percentages, and episode numbers", () => {
    expect(fmtDuration(65)).toBe("1:05");
    expect(fmtPct(0.125)).toBe("12.5%");
    expect(pad2(7)).toBe("07");
  });

  it("shortens long text without exceeding the requested width", () => {
    expect(shorten("A long episode title", 10)).toBe("A long ep…");
    expect(shorten("Title", 10)).toBe("Title");
  });
});

describe("series bucketing", () => {
  it("keeps daily points when weekly bucketing is disabled", () => {
    const input = [point("2026-10-12", 4, 1), point("2026-10-13", 6, 2)];
    expect(bucketSeries(input, false)).toEqual([
      { label: "Oct 12", views: 4, subs: 1 },
      { label: "Oct 13", views: 6, subs: 2 },
    ]);
  });

  it("aggregates points by Monday-based calendar week", () => {
    const input = [
      point("2026-10-11", 4, 1),
      point("2026-10-12", 6, 2),
      point("2026-10-18", 3, 1),
    ];
    expect(bucketSeries(input, true)).toEqual([
      { label: "Oct 5", views: 4, subs: 1 },
      { label: "Oct 12", views: 9, subs: 3 },
    ]);
  });
});

function point(day: string, views: number, subs: number): SeriesPoint {
  return { day, views, subs, watchHours: 0, ctr: 0, likes: 0 };
}