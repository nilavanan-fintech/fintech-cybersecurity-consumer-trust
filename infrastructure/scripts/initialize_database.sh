#!/usr/bin/env bash
# Apply schema, migrations and seed data to a PostgreSQL instance (outside Docker).
# Inside Docker Compose the same files are applied automatically by the postgres image.
# Usage: DATABASE_URL=postgresql://user:pass@localhost:5432/fintech_research ./initialize_database.sh
set -euo pipefail
: "${DATABASE_URL:?set DATABASE_URL}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT/database/schema.sql"
for f in "$ROOT"/database/migrations/*.sql; do psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"; done
for f in "$ROOT"/database/seed_data/*.sql; do psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"; done
echo "database initialised"
