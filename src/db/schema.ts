import {
  date,
  index,
  integer,
  jsonb,
  pgTable,
  serial,
  text,
  timestamp,
  uniqueIndex,
} from "drizzle-orm/pg-core";

/**
 * YouTube Master Content — one row per Short / episode.
 * Columns mirror the master table spec:
 *   Episode, Date, Title, Status, Collection, Sound / Music, Effects,
 *   Subtitles, Thumbnail (+ duration for Shorts).
 */
export const youtubeContent = pgTable(
  "youtube_content",
  {
    id: serial("id").primaryKey(),
    episode: integer("episode").notNull().unique(),
    date: date("date", { mode: "string" }).notNull(),
    title: text("title").notNull(),
    status: text("status").notNull().default("Draft"),
    collection: text("collection").notNull(),
    soundMusic: text("sound_music").notNull().default(""),
    effects: text("effects").notNull().default(""),
    subtitles: text("subtitles").notNull().default("None"),
    thumbnail: text("thumbnail").notNull().default(""),
    durationSec: integer("duration_sec").notNull().default(45),
    /** On-screen script used by the FFmpeg renderer: { command, tip, audio }. */
    script: jsonb("script").$type<{ command: string; tip: string; audio: boolean }>(),
    /** none | queued | running | done | failed */
    renderStatus: text("render_status").notNull().default("none"),
    renderProgress: integer("render_progress").notNull().default(0),
    renderError: text("render_error"),
    /** Relative to the render root, e.g. "21/video.mp4". Null until a render succeeds. */
    videoPath: text("video_path"),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [
    index("youtube_content_date_idx").on(t.date),
    index("youtube_content_collection_idx").on(t.collection),
  ],
);

/** Daily performance per episode — powers every chart and KPI on the dashboard. */
export const contentDailyStats = pgTable(
  "content_daily_stats",
  {
    id: serial("id").primaryKey(),
    contentId: integer("content_id")
      .notNull()
      .references(() => youtubeContent.id, { onDelete: "cascade" }),
    day: date("day", { mode: "string" }).notNull(),
    views: integer("views").notNull().default(0),
    impressions: integer("impressions").notNull().default(0),
    watchSeconds: integer("watch_seconds").notNull().default(0),
    likes: integer("likes").notNull().default(0),
    subsGained: integer("subs_gained").notNull().default(0),
  },
  (t) => [
    uniqueIndex("content_daily_stats_uniq").on(t.contentId, t.day),
    index("content_daily_stats_day_idx").on(t.day),
  ],
);
