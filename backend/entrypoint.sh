#!/usr/bin/env sh
#
# Container entrypoint: bring the database up to date, make sure the knowledge
# graph exists, then hand off to the CMD (uvicorn).
#
# Without this, a fresh `docker compose up` produced a running API on top of an
# empty database: no tables, no concepts, and a dashboard that rendered nothing.
# The README never mentioned the migrate/seed steps, so there was no way to
# discover them short of reading the source.
#
# Set AUTO_MIGRATE=0 to skip straight to the CMD — used by the CI smoke test,
# which starts the image with no database attached just to poll /health.
set -e

if [ "${AUTO_MIGRATE:-1}" = "1" ]; then
  echo "[entrypoint] waiting for database..."
  python - <<'PY'
import sys
import time

from sqlalchemy import create_engine, text

from app.config import settings

url = settings.get_database_url()
for attempt in range(1, 31):
    try:
        with create_engine(url).connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[entrypoint] database reachable after {attempt} attempt(s)")
        break
    except Exception as exc:  # noqa: BLE001 - any failure here means "not ready yet"
        if attempt == 30:
            print(f"[entrypoint] database unreachable: {exc}", file=sys.stderr)
            sys.exit(1)
        time.sleep(2)
PY

  echo "[entrypoint] applying migrations..."
  alembic upgrade head

  # seed_graph is idempotent — it counts existing nodes and returns early.
  echo "[entrypoint] seeding knowledge graph..."
  python -m app.data.seed_graph
else
  echo "[entrypoint] AUTO_MIGRATE=0 — skipping migrate and seed"
fi

exec "$@"
