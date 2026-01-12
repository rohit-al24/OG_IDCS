#!/usr/bin/env python3
"""
Upload Django fixture (data.json) to Supabase via the REST API using the service_role key.

Usage:
  export SUPABASE_URL='https://pahfkfelkfamzycdioeb.supabase.co'
  export SUPABASE_SERVICE_ROLE='...'
  python scripts/upload_to_supabase_rest.py data.json

Notes:
- The Supabase database must already have the tables (run the SQL from supabase_schema.sql in the Supabase SQL editor first).
- This script will attempt multiple passes to resolve foreign-key ordering by skipping rows that error and retrying.
- Keep an eye on the output; rotate the service_role key after use.
"""
import sys
import json
import time
import requests
from urllib.parse import urljoin


def load_fixture(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def model_to_table(model_label):
    # model_label is like 'app.ModelName' or 'app.modelname'
    app, model = model_label.split('.')
    return f"{app.lower()}_{model.lower()}"


def try_post_row(base_url, headers, table, payload):
    url = f"{base_url}/rest/v1/{table}"
    # Use Prefer header to try to do upsert if duplicate
    # We use resolution=merge-duplicates to merge on conflict
    hdrs = headers.copy()
    hdrs['Prefer'] = 'resolution=merge-duplicates'
    r = requests.post(url, headers=hdrs, json=payload, timeout=30)
    return r


def main():
    if len(sys.argv) < 2:
        print("Usage: upload_to_supabase_rest.py <data.json>")
        sys.exit(1)
    fixture_path = sys.argv[1]
    base_url = os.environ.get('SUPABASE_URL') or os.environ.get('PROJECT_URL')
    service_role = os.environ.get('SUPABASE_SERVICE_ROLE') or os.environ.get('SERVICE_ROLE')
    if not base_url or not service_role:
        print("Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE environment variables.")
        sys.exit(1)

    data = load_fixture(fixture_path)
    print(f"Loaded {len(data)} fixture objects from {fixture_path}")

    headers = {
        'apikey': service_role,
        'Authorization': f'Bearer {service_role}',
        'Content-Type': 'application/json'
    }

    # Group items by table
    items_by_table = {}
    for item in data:
        table = model_to_table(item['model'])
        payload = item.get('fields', {}).copy()
        # include primary key if present
        if 'pk' in item:
            payload['id'] = item['pk']
        items_by_table.setdefault(table, []).append((item['model'], payload))

    total = sum(len(v) for v in items_by_table.values())
    print(f"Prepared {total} rows for {len(items_by_table)} tables")

    remaining = []
    for table, rows in items_by_table.items():
        for model, payload in rows:
            remaining.append((table, payload))

    max_passes = 12
    pass_no = 0
    successes = 0
    failures = []

    while remaining and pass_no < max_passes:
        pass_no += 1
        print(f"Pass {pass_no}: attempting to insert {len(remaining)} rows")
        next_remaining = []
        made_progress = False
        for table, payload in remaining:
            try:
                r = try_post_row(base_url, headers, table, payload)
            except Exception as e:
                print(f"Network/error posting to {table}: {e}")
                next_remaining.append((table, payload))
                continue
            if r.status_code in (200, 201):
                successes += 1
                made_progress = True
            else:
                txt = r.text.strip()
                # If table not found (404), it's a schema issue — abort early
                if r.status_code == 404:
                    print(f"ERROR: Table {table} not found in Supabase (404). Make sure you ran supabase_schema.sql in SQL editor.)")
                    failures.append((table, payload, r.status_code, txt))
                else:
                    # Likely FK/constraint error; keep for another pass
                    print(f"Skipped {table} id={payload.get('id')} status={r.status_code}: {txt[:200]}")
                    next_remaining.append((table, payload))
        if not made_progress:
            print("No progress made this pass; stopping to avoid infinite loop")
            break
        remaining = next_remaining
        time.sleep(0.3)

    if remaining:
        print(f"Finished with {len(remaining)} rows remaining after {pass_no} passes")
        # Save remaining to a file for debugging
        with open('remaining_failed.json', 'w', encoding='utf-8') as out:
            json.dump([{'table': t, 'payload': p} for t, p in remaining], out, default=str)
        print("Wrote remaining_failed.json for inspection")
    print(f"Uploaded {successes} rows; {len(remaining)} failed or deferred")
    if failures:
        print("Some failures encountered:")
        for f in failures[:20]:
            table, payload, code, msg = f
            print(table, payload.get('id'), code, msg[:200])


if __name__ == '__main__':
    import os
    main()
