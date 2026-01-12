Migration to Supabase (Postgres) — instructions

This document explains how to switch the Django project to use Supabase Postgres as the primary database and migrate the current sqlite data.

Important safety notes
- Do not commit secrets to the repository. Use a local `.env` file or CI secrets.
- If you share service_role keys with anyone (including this workspace), rotate them after use.

Pre-steps (in Supabase UI)
1. Open your Supabase project → SQL Editor.
2. Create a new query and paste the `supabase_schema.sql` file contents. Run it to create all tables and indexes on the Supabase database.
   - This must be done before any REST-based inserts if you will use the REST upload path.

Recommended path (direct DB access — preferred)
1. Run migrations and load data directly from a machine that can connect to Supabase on port 5432.
2. Steps to run locally (from repository root):

```bash
# create virtualenv and activate
python -m venv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# point Django at Supabase Postgres (example)
export DATABASE_URL='postgresql://postgres:Idcssupabase@db.pahfkfelkfamzycdioeb.supabase.co:5432/postgres'

# run migration helper (this will dump local sqlite to data.json, run migrate on Supabase, loaddata, and fix sequences)
chmod +x scripts/migrate_to_supabase.sh
./scripts/migrate_to_supabase.sh
```

- If `loaddata` fails due to FK ordering, run the REST upload (see alternative path) or contact me with the error output and I'll generate an ordered transfer.

Alternative path (REST upload using service_role)
1. Ensure you ran `supabase_schema.sql` in the Supabase SQL editor.
2. Export REST credentials locally:

```bash
export SUPABASE_URL='https://pahfkfelkfamzycdioeb.supabase.co'
export SUPABASE_SERVICE_ROLE='your-service-role-key'
python3 scripts/upload_to_supabase_rest.py data.json
```

This method uses the PostgREST endpoint and will attempt multiple passes to resolve FK ordering. It may leave some rows in `remaining_failed.json` for manual inspection.

After migration
- Verify record counts in Supabase vs sqlite (a few spot checks): users, students, staff, etc.
- Verify media files: the DB will contain filenames/paths referencing files in `media/`. You need to copy `media/` contents to a place that your production app can serve — either object storage (S3/Spaces) or the same server filesystem. The migration scripts do not move media files.
- Rotate any keys you temporarily used.

If you want me to finish the upload from here
- I can retry the REST upload if you provide a valid service_role key here (note security) and confirm `supabase_schema.sql` has been applied. Or you can run the direct DB migration locally using the wrapper above.

If anything fails, paste the exact error and I'll produce a targeted fix (ORM-based ordered export/import, or SQL `INSERT` batches).
