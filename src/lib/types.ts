export type KpiKey = "views" | "watchHours" | "subs" | "ctr" | "likes";

export interface KpiPair {
  value: number;
  prev: number;
}

export interface SeriesPoint {
  day: string;
  views: number;
  watchHours: number;
  subs: number;
  ctr: number;
  likes: number;
}

export interface OnScreenScript {
  command: string;
  tip: string;
  audio: boolean;
}

export interface ContentRow {
  id: number;
  episode: number;
  date: string;
  title: string;
  status: string;
  collection: string;
  soundMusic: string;
  effects: string;
  subtitles: string;
  thumbnail: string;
  durationSec: number;
  script: OnScreenScript | null;
  renderStatus: "none" | "queued" | "running" | "done" | "failed";
  renderProgress: number;
  renderError: string | null;
  videoPath: string | null;
  hasVideo: boolean;
  views: number;
  impressions: number;
  likes: number;
  subs: number;
}

export interface DashboardData {
  range: { from: string; to: string; days: number };
  kpis: Record<KpiKey, KpiPair>;
  series: SeriesPoint[];
  rows: ContentRow[];
  generatedAt: string;
}

export interface RenderState {
  id: number;
  renderStatus: ContentRow["renderStatus"];
  renderProgress: number;
  renderError: string | null;
  hasVideo: boolean;
}