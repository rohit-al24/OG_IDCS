#!/usr/bin/env bash
set -euo pipefail

# Wrapper to run the full migration locally. Run this on a machine that can
# reach Supabase on port 5432 (your laptop or a VM with internet egress).
#
# Usage:
#   1. Copy .env.example to .env and set DATABASE_URL to your Supabase URL
#   2. ./scripts/run_migration_locally.sh

ROOT_DIR=$(dirname "$(dirname "${BASH_SOURCE[0]}")")
cd "$ROOT_DIR"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "Please set DATABASE_URL in your environment or export it before running."
  echo "Example: export DATABASE_URL='postgresql://postgres:password@host:5432/postgres'"
  exit 1
fi

echo "Creating virtualenv (if .venv doesn't exist)..."
if [ ! -d .venv ]; then
  python -m venv .venv
fi

# Activate virtualenv for this script
# shellcheck disable=SC1091
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Ensure we use sqlite as the source for dump: temporarily unset DATABASE_URL when dumping
echo "Creating fixture from local sqlite..."
env -u DATABASE_URL python manage.py dumpdata --natural-foreign --natural-primary --exclude auth.permission --exclude contenttypes > data.json

echo "Running migrations on Supabase (DATABASE_URL) ..."
python manage.py migrate --noinput

echo "Loading data.json into Supabase..."
python manage.py loaddata data.json

echo "Fixing Postgres sequences..."
python scripts/fix_postgres_sequences.py "$DATABASE_URL"

echo "Migration script finished. Check Supabase and rotate any temporary keys used."
