# FastAPI Backend

Layered architecture — every layer is independently testable:

```
app/
├── main.py          # app factory + lifespan (tables → seed → render worker)
├── core/            # settings (YTCM_* env), domain constants, error taxonomy
├── api/routes/      # thin HTTP routers: health, meta, dashboard, content, renders
├── services/        # business logic: analytics (KPI math), content (CRUD rules)
├── db/              # SQLAlchemy models, sessions, deterministic seed
├── rendering/       # FFmpeg orchestration: queue, renderer, storage, arg builder
└── schemas/         # Pydantic contracts (camelCase JSON for the frontend)
```

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Configuration (all optional — see `.env.example`): `YTCM_DATABASE_URL`,
`YTCM_RENDER_ROOT`, `YTCM_SEED_ON_STARTUP`, `YTCM_CORS_ORIGINS`.
No `YTCM_DATABASE_URL`? SQLite at `backend/data/youtube.db`.

## Test

```bash
.venv/bin/python -m pytest        # full suite
.venv/bin/ruff check app tests    # lint
```

Tests run against a temporary SQLite database per test with a scripted
`FakeRenderer` (no FFmpeg needed); the video-streaming tests exercise real
HTTP Range semantics through the actual app + lifespan.

## Design notes

- **Same schema as before** — table/column names match the original Drizzle
  schema, so a database created by the previous Next.js backend keeps working.
- **camelCase JSON** — Pydantic alias generators produce the exact dialect the
  frontend types expect (`soundMusic`, `durationSec`, `renderStatus`, …);
  `tests/test_contract.py` fails loudly if the two drift apart.
- **Render queue** — one asyncio worker, one FFmpeg at a time; progress is
  throttled to ~1 percentage point per DB write; deleted episodes cancel
  their own progress writes.
- **Errors** — domain errors carry HTTP status codes (`404` missing,
  `400` validation, `503` FFmpeg unavailable) and always serialize as
  `{"error": "…"}` which the frontend toasts directly.
