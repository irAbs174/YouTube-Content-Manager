"""FastAPI backend for YouTube Content Manager.

Layers:
    api/routes  — HTTP surface (thin: validate + delegate)
    services    — business logic (analytics, content CRUD)
    db          — SQLAlchemy models, sessions, deterministic seed
    rendering   — FFmpeg render orchestration (queue, renderer, storage)
    schemas     — Pydantic request/response contracts (camelCase JSON)
"""

__version__ = "0.2.0"
