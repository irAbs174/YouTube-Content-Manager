# System Logic
    Goal: ==> A UNIQUE & Minimal YouTube Managment Application <==

    | Stack |  FastAPI (backend), SQLAlchemy, Next.js + React (frontend), Tailwind CSS, PostgreSQL (SQLite fallback), FFmpeg (rendering), Docker Compose (orchestration). 
    | CI/CD |  Github Actions — pytest (ruff) + vitest (eslint, tsc) on every push/PR
    | Release | 0.3.0 — Authenticated Studio
    | Version | 0.3.0

## YouTube Master Content
    Workbook: `youTube-master-content-managment-v001.xlsx` (9 sheets) at repo root — source of truth.
    The Main YouTube Database Table (`youtube_main`, legacy `youtube_content` alias)

    Normalized columns (from YouTube Main 📌):
       1. Episode — `series_id` FK + `episode_number` (unique per series per user), display `"{series.name} #{n}"`
       2. Date — nullable `date` (Excel serial)
       3. Title — via `Contents 🖊️` Senario Lookup (XLOOKUP)
       4. Status → `visibility` (select list: `Public` | `Schedule` | `Private` | `Draft` | `Not List`)
       5. Collection — `collection_id` FK → `collections` (plus legacy `collection` string for compat)
       6. Sound Effects — `sound_effects` bool
       7. Music — `music` bool (split from legacy `sound_music` string)
       8. Subtitles — `subtitles_count` int (COUNTIF `Subtitles 🔍`), legacy `subtitles` string kept
       9. Tumbnaill — `thumbnail_ready` bool (legacy `thumbnail` string kept)
      10. Duration — `duration_sec` (5–180, sum of scenes when present)
      11. Scenes — `episode_scenes` (position, duration_sec, command, tip, audio, notes) — Lab/emulator primitive
      12. Series — `series` per-user (`name` unique per user)
      13. Collections — `collections` lookup (color, sounds tuple)
      14. Auth — `users` (`email`, `password_hash` bcrypt) + `sessions` (token_hash sha256, expires_at)
      15. Render pipeline (render_status, render_progress, render_error, video_path)
      16. On-screen script (command, tip, audio) — transitional JSON, replaced by scenes
    17. Library spec places — `content_items` (Contents 🖊️), `subtitles` (Subtitles 🔍),
        `languages` (Languages 🌍), `assets` (Assets 👁️👁️), plus the Collections 📃
        metadata (`code` · `title` · `description` · `type` · `share_link`), the
        Scenes 🎬 script fields (`title` · `hook` · `scenario` · `body`) and the
        Episodes ⏭️ `shared_link`.  `GET /api/library/places` publishes the column
        spec; the frontend renders every place from it.

    Companion table `content_daily_stats` (views, impressions, watch_seconds,
    likes, subs_gained per day) powers every chart and KPI — per-user scoped in analytics.

    Seed: deterministic `random.Random(42)` — demo user `demo@ytcm.test` + one `Seed Series` with 26 `youtube_main` rows (visibility Public/Private, legacy strings kept) + 180 days of decaying stats per episode. New users start empty; only empty DB seeds demo data.

## Cells Formulation
    Dashboard KPIs compare the selected window against the immediately
    preceding window of equal length ("vs prior Nd"). Rows aggregate each
    episode's daily stats across the window; the series aggregates the whole
    channel (older episodes keep earning views inside the window). Per-user filtering when authenticated.

## PIP Line's
    Single-scene: POST /api/content (render=true) → queued → async worker → FFmpeg 1080x1920
    (command card + tip card + optional generated audio, progress via
    -progress pipe:1) → thumbnail extraction → done | failed (retryable).

    Multi-scene: Lab posts `scenes[]` → queue builds `RenderSpec(scenes)` → FfmpegRenderer renders each scene to temp `part_*.mp4` (drawtext via textfile=) then `ffmpeg -f concat -safe 0 -i list.txt -c copy` (fallback re-encode) → `video.mp4` + thumbnail. Progress is weighted per scene (overall 0..100). Emulator is client-only JS-timed playback (no FFmpeg).

## Project Phases
    [x] Phase 1 — Shorts analytics dashboard + master content table
    [x] Phase 2 — FastAPI backend, layered (routes → services → db), tested
    [x] Phase 3 — FFmpeg render orchestration with live progress
    [x] Phase 3.5 — Authenticated Studio: httpOnly bcrypt sessions, per-user scoping, series/collections normalization, scenes + Lab/Emulator/Library, multi-scene concat
    [ ] Phase 4 — Google Drive sync, scheduling, YouTube Data API upload

## About Project
    Next.js frontend proxies /api/* to the FastAPI backend (no CORS, no
    hardcoded hosts in the browser; CORS allow_credentials for direct httpx). The backend owns persistence and the
    render queue; the frontend owns presentation and client logic only.

    Auth: open register/login — email+password, `ytcm_session` httpOnly SameSite=Lax, 14d TTL. SSR fetches forward `Cookie`; client uses `credentials: include`. `/api/health` + `/api/meta` stay public; dashboard/content/renders/series/scenes are per-user (fallback to demo user for legacy unauth tests).

    Surfaces: Home (card-only KPIs + visibility + readiness + Lab/Emulator/Library + last 3), Lab (`/lab` + `/lab/[id]` three-column: scene stack | 9:16 stage | YouTube Main meta, autosave), Emulator (`/emulator` picker + `/emulator/[id]` phone bezel + Shorts chrome), Library (`/library` tabs = the workbook's spec places: Main Library, Contents, Scenes, Episodes, Collections, Languages, Assets, Subtitle — each with the sheet's exact columns, live select lists and in-place editing).

## Development Data Flow Diagram
    browser → Next.js (SSR + rewrites) → FastAPI → SQLAlchemy → Postgres/SQLite
                                      ↘ render queue (FFmpeg concat per scene) → render_root/
                                      ↘ users/sessions → series/collections → youtube_main → episode_scenes
                                      ↘ library places → content_items · subtitles · languages · assets

## Deployment
    docker compose up --build  (db + api + web) · see README.md for local dev
    Requires `ffmpeg` for rendering; without it render endpoints 503. Env see `backend/.env.example` (`YTCM_SESSION_SECRET` must be set in prod).
