# YouTube Content Manager

YouTube Shorts content-management logic **for now** → goal: YouTube Master Content Management.

A minimal authenticated studio for Shorts: card-only Home, 3-column Episode Creation Lab with live 9:16 stage, dedicated Shorts-chrome Emulator, and Library mirroring the YouTube Master workbook (9 sheets) — with HTTP-only session auth, per-user scoping, scene-based editing, and multi-scene FFmpeg concat.

```
┌──────────────────────────┐        /api/* (rewrites)        ┌──────────────────────────┐
│  Next.js 16 (frontend)   │ ──────────────────────────────▶ │  FastAPI (backend)       │
│  Home · Lab · Emulator  │      same-origin proxy +        │  routes → services → db  │
│  Library · auth gate   │      SSR fetch on first paint   │  render queue (FFmpeg)   │
└──────────────────────────┘                                 └───────────┬──────────────┘
                                                                         │ SQLAlchemy
                                                              ┌──────────▼──────────────┐
                                                              │ PostgreSQL / SQLite     │
                                                              │ users · sessions · series│
                                                              │ youtube_main · episode_scenes │
                                                              │ content_daily_stats     │
                                                              └─────────────────────────┘
```

Workbook source of truth: `youTube-master-content-managment-v001.xlsx` (+ preview png) at repo root — 9 sheets (YouTube Main 📌, Contents 🖊️, Episodes ⏭️, Scenses 🎬, Languages 🌍, Assets, Subtitles 🔍, Collections 📃, Body Content). `youtube_main` is normalized from `Episode/Data/Title/Status/Collection/Sound Effects/Music/Subtitles/Tumbnaill` with `series` + `collections` lookups, `episode_scenes` for Lab/Emulator, and `users/sessions` for auth.

## Quick start (local, zero config)

```bash
make install   # backend venv + npm packages
make dev       # FastAPI on :8000 + Next.js on :3000, managed together
```

Open http://localhost:3000. The backend seeds deterministic sample data on first boot
(26 episodes / 180 days of daily stats) and falls back to SQLite when no Postgres is
configured — `DATABASE_URL`/`YTCM_DATABASE_URL` switches it to Postgres.

> Rendering needs `ffmpeg` on the machine. Without it, everything else works and the
> render endpoints answer a friendly 503 that the UI surfaces in the dialog.

## Full stack (Docker Compose)

```bash
docker compose up --build
# dashboard → http://localhost:3000 · API docs → http://localhost:8000/docs
```

## Project layout

| Path                    | What lives here                                                  |
| ----------------------- | ---------------------------------------------------------------- |
| `src/app`, `src/components` | Next.js dashboard UI (client components, charts, table)      |
| `src/lib`               | Frontend logic: shared types, constants, date/format helpers, series bucketing |
| `backend/app/api`       | HTTP surface — thin routers that validate and delegate           |
| `backend/app/services`  | Business logic: analytics/KPI math, episode CRUD rules           |
| `backend/app/db`        | SQLAlchemy models (mirrors the original schema), seeding, sessions |
| `backend/app/rendering` | FFmpeg orchestration: queue → renderer → storage                 |
| `backend/app/schemas`   | Pydantic request/response contracts (camelCase JSON)             |
| `backend/tests`         | pytest suite — API, services, queue, streaming, contracts        |
| `src/lib/__tests__`     | vitest suite — frontend logic modules                             |

## API

| Method & path                      | Purpose                                          |
| ---------------------------------- | ------------------------------------------------ |
| `GET  /api/health`                 | liveness + DB check                              |
| `GET  /api/meta`                   | visibilities / collections / options (single source) |
| `POST /api/auth/register`          | create account + set `ytcm_session` httpOnly cookie |
| `POST /api/auth/login`             | login + set cookie                               |
| `POST /api/auth/logout`            | clear session                                    |
| `GET  /api/auth/me`                | current user or 401                              |
| `GET  /api/series`                 | list user's series                               |
| `POST /api/series`                 | create series                                    |
| `GET  /api/dashboard`              | KPIs, daily series, filtered episode rows (per-user) |
| `POST /api/content`                | create episode (seriesName/episodeNumber/visibility/soundEffects/music…) + optional `scenes[]` |
| `PATCH/DELETE /api/content/:id`    | update visibility/title/collection… · delete + cascade stats/scenes |
| `GET/POST /api/content/:id/scenes` | list / create scenes                             |
| `PATCH/DELETE /api/content/:id/scenes/:sceneId` | update / delete scene (repacks positions) |
| `PUT  /api/content/:id/scenes/reorder` | reorder scenes `{orderedIds}`                 |
| `POST /api/content/:id/render`     | (re)queue FFmpeg render (multi-scene concat)     |
| `GET  /api/content/:id/video`      | stream MP4 with HTTP Range support               |
| `GET  /api/content/:id/thumbnail`  | extracted poster frame                           |
| `GET  /api/renders?ids=1,2`        | lightweight render-state polling (per-user)      |

Interactive docs: http://localhost:8000/docs (OpenAPI).

## Tests

```bash
make test            # everything
make test-backend    # pytest  (82 tests: API, analytics, queue, streaming, contracts)
make test-frontend   # vitest  (36 tests: dates, format, series, constants)
make lint            # ruff + eslint
make typecheck       # tsc --noEmit
```

CI runs the same matrix on every push/PR (`.github/workflows/ci.yml`).

## Rendering pipeline

`POST /api/content` (or `POST /api/content/:id/render`) → episode marked `queued` →
async worker picks it up → FFmpeg renders a 1080×1920 Short (on-screen command card +
tip card, optional generated audio) with live progress parsed from `-progress pipe:1` →
thumbnail extracted → row marked `done` (or `failed` with the captured error). The
dashboard polls `/api/renders` every 1.5 s while jobs are in flight.
