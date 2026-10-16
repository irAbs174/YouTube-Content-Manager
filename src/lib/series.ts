import type { SeriesPoint } from "./types";

export interface TrendPoint {
  label: string;
  views: number;
  subs: number;
}

const LABEL_FORMAT = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  timeZone: "UTC",
});

export function bucketSeries(series: SeriesPoint[], weekly: boolean): TrendPoint[] {
  if (!weekly) {
    return series.map((point) => ({
      label: formatLabel(point.day),
      views: point.views,
      subs: point.subs,
    }));
  }

  const buckets = new Map<string, TrendPoint>();
  for (const point of series) {
    const day = new Date(`${point.day}T00:00:00.000Z`);
    const weekday = (day.getUTCDay() + 6) % 7;
    day.setUTCDate(day.getUTCDate() - weekday);
    const week = day.toISOString().slice(0, 10);
    const bucket = buckets.get(week);
    if (bucket) {
      bucket.views += point.views;
      bucket.subs += point.subs;
    } else {
      buckets.set(week, {
        label: formatLabel(week),
        views: point.views,
        subs: point.subs,
      });
    }
  }
  return [...buckets.values()];
}

function formatLabel(day: string): string {
  const date = new Date(`${day}T00:00:00.000Z`);
  return Number.isNaN(date.getTime()) ? day : LABEL_FORMAT.format(date);
}