# System Logic
    Goal: ==> A UNIQUE & Minimal YouTube Managment Application <==

    | Stack |  FastAPI (backend), SQLAlchemy, Next.js + React (frontend), Tailwind CSS, PostgreSQL (SQLite fallback), FFmpeg (rendering), Docker Compose (orchestration). 
    | CI/CD |  Github Actions — pytest (ruff) + vitest (eslint, tsc) on every push/PR
    | Release | Null
    | Version | 0.2.0

## YouTube Master Content
    The Main YouTube Database Table (`youtube_content`)
    
    Columns:
       1. Episode (unique, auto-assigned max+1)
       2. Date
       3. Title
       4. Status (Draft → Scripting → Recording → Editing → Scheduled → Published)
       5. Collection (Linux Basics / Network Hacking / Privilege Escalation / OSINT / Scripting & Automation)
       6. Sound Effects / Music
       7. Effects
       8. Subtitles
       9. Tumbnaill
      10. Render pipeline (render_status, render_progress, render_error, video_path)
      11. On-screen script (command, tip, audio) — consumed by the FFmpeg renderer

    Companion table `content_daily_stats` (views, impressions, watch_seconds,
    likes, subs_gained per day) powers every chart and KPI.

## Cells Formulation
    Dashboard KPIs compare the selected window against the immediately
    preceding window of equal length ("vs prior Nd"). Rows aggregate each
    episode's daily stats across the window; the series aggregates the whole
    channel (older episodes keep earning views inside the window).

## PIP Line's
    POST /api/content (render=true) → queued → async worker → FFmpeg 1080x1920
    (command card + tip card + optional generated audio, progress via
    -progress pipe:1) → thumbnail extraction → done | failed (retryable).

## Project Phases
    [x] Phase 1 — Shorts analytics dashboard + master content table
    [x] Phase 2 — FastAPI backend, layered (routes → services → db), tested
    [x] Phase 3 — FFmpeg render orchestration with live progress
    [ ] Phase 4 — Google Drive sync, scheduling, YouTube Data API upload

## About Project
    Next.js frontend proxies /api/* to the FastAPI backend (no CORS, no
    hardcoded hosts in the browser). The backend owns persistence and the
    render queue; the frontend owns presentation and client logic only.

## Development Data Flow Diagram
    browser → Next.js (SSR + rewrites) → FastAPI → SQLAlchemy → Postgres/SQLite
                                      ↘ render queue → FFmpeg → render_root/

## Deployment
    docker compose up --build  (db + api + web) · see README.md for local dev
