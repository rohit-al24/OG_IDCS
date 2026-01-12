#!/usr/bin/env bash
set -euo pipefail

# migrate_to_supabase.sh
# Usage:
#   1. Ensure you have a working virtualenv with dependencies installed.
#   2. Export DATABASE_URL before running, e.g.:
#        export DATABASE_URL='postgresql://postgres:PW@host:5432/postgres'
#   3. Run:
#        ./scripts/migrate_to_supabase.sh
#
# This script will:
#  - create a dump of the current sqlite (data.json)
#  - run migrations against the DATABASE_URL (Supabase)
#  - load the fixture into Supabase
#  - run a Python helper to fix Postgres sequences

ROOT_DIR=$(dirname "$(dirname "${BASH_SOURCE[0]}")")
cd "$ROOT_DIR"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: Please set DATABASE_URL before running this script."
  echo "Example: export DATABASE_URL='postgresql://postgres:password@host:5432/postgres'"
  exit 1
fi

# Ensure we use sqlite as the source for dump: temporarily unset DATABASE_URL when dumping
echo "Creating fixture from local sqlite..."
	env -u DATABASE_URL python manage.py dumpdata --natural-foreign --natural-primary --exclude auth.permission --exclude contenttypes > data.json

echo "Fixture written to data.json (size: $(stat -c%s data.json) bytes)"

# Run migrations on Supabase (default will be DATABASE_URL)
echo "Running migrations on Supabase (DATABASE_URL) ..."
python manage.py migrate --noinput

# Load fixture into Supabase
echo "Loading data.json into Supabase (this may take a while)..."
python manage.py loaddata data.json

# Fix Postgres sequences (run the python helper)
echo "Fixing postgres sequences (setting nextval to max(id)+1 where applicable)..."
python scripts/fix_postgres_sequences.py "$DATABASE_URL"

echo "Done. Verify your Supabase project now. If you used any sensitive keys here, rotate them after migration."