#!/usr/bin/env python3
"""
Fix Postgres sequences by setting each sequence to (max(id) + 1) for tables that have an integer primary key named `id`.
Usage: python scripts/fix_postgres_sequences.py postgresql://user:pass@host:port/dbname
"""
import sys
import urllib.parse

try:
    import psycopg2
except ImportError:
    print("psycopg2 not installed. Install it with: pip install psycopg2-binary")
    sys.exit(1)


def fix_sequences(dsn):
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()

    # find user tables
    cur.execute("""
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_type='BASE TABLE' AND table_schema NOT IN ('pg_catalog','information_schema');
    """)

    tables = cur.fetchall()
    for schema, table in tables:
        # check if table has integer primary key column named id
        cur.execute("""
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = %s::regclass AND i.indisprimary;
        """, (f"{schema}.{table}",))
        pk_cols = cur.fetchall()
        if not pk_cols:
            continue
        pk_col = pk_cols[0][0]
        if pk_col != 'id':
            # only handle simple id PK
            continue
        # get max(id)
        cur.execute(f"SELECT MAX(id) FROM \"{schema}\".\"{table}\"")
        mx = cur.fetchone()[0]
        if mx is None:
            next_val = 1
        else:
            next_val = int(mx) + 1
        # attempt to find the sequence name
        cur.execute("""
        SELECT pg_get_serial_sequence(%s::text, %s::text);
        """, (f"{schema}.{table}", pk_col))
        seq = cur.fetchone()[0]
        if not seq:
            # no sequence found
            continue
        cur.execute(f"SELECT setval(%s, %s, false);", (seq, next_val))
        print(f"Set sequence {seq} to {next_val} for {schema}.{table}")

    cur.close()
    conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: fix_postgres_sequences.py <DATABASE_URL>")
        sys.exit(1)
    dsn = sys.argv[1]
    fix_sequences(dsn)
