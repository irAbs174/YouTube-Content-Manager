# YouTube Content Manager

YouTube Shorts content-management logic **for now** → goal: YouTube Master Content Management.

A unique & minimal YouTube management application: a Next.js analytics dashboard over a
FastAPI backend, with FFmpeg-orchestrated Short rendering and a fully tested, layered codebase.

```
┌──────────────────────────┐        /api/* (rewrites)        ┌──────────────────────────┐
│  Next.js 16 (frontend)   │ ──────────────────────────────▶ │  FastAPI (backend)       │
│  dashboard · charts ·    │      same-origin proxy +        │  routes → services → db  │
│  master content table    │      SSR fetch on first paint   │  render queue (FFmpeg)   │
└──────────────────────────┘                                 └───────────┬──────────────┘
                                                                         │ SQLAlchemy
                                                              ┌──────────▼──────────────┐
                                                              │ PostgreSQL / SQLite     │
                                                              │ youtube_content         │
                                                              │ content_daily_stats     │
                                                              └─────────────────────────┘
```

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
| `GET  /api/meta`                   | statuses / collections / options (single source) |
| `GET  /api/dashboard`              | KPIs, daily series, filtered episode rows        |
| `POST /api/content`                | create episode (optionally queue a render)       |
| `PATCH/DELETE /api/content/:id`    | update status/title · delete + cascade stats     |
| `POST /api/content/:id/render`     | (re)queue an FFmpeg render                       |
| `GET  /api/content/:id/video`      | stream MP4 with HTTP Range support               |
| `GET  /api/content/:id/thumbnail`  | extracted poster frame                           |
| `GET  /api/renders?ids=1,2`        | lightweight render-state polling                 |

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
