#!/usr/bin/env bash
# Orchestrate the full dev stack: FastAPI backend + Next.js frontend.
#   ./scripts/dev.sh            — both, with logs interleaved
# The script waits for backend health before starting the frontend and
# tears both processes down on Ctrl-C.
set -euo pipefail
cd "$(dirname "$0")/.."

BACKEND_DIR="backend"
VENV="$BACKEND_DIR/.venv"
BACKEND_URL="${API_ORIGIN_INTERNAL:-http://127.0.0.1:8000}"

if [ ! -x "$VENV/bin/uvicorn" ]; then
  echo "▶ backend venv missing — run: make install"
  exit 1
fi

pids=()
cleanup() {
  echo ""
  echo "▶ shutting down..."
  for pid in "${pids[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "▶ starting FastAPI backend on :8000"
(cd "$BACKEND_DIR" && "$VENV/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000) &
pids+=($!)

echo -n "▶ waiting for backend health"
for _ in $(seq 1 60); do
  if curl -fsS "$BACKEND_URL/api/health" >/dev/null 2>&1; then
    echo " ok"
    break
  fi
  echo -n "."
  sleep 0.5
done

echo "▶ starting Next.js frontend on :3000"
npm run dev &
pids+=($!)

wait
