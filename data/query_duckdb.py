#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

import duckdb

BLOCKED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|"
    r"COPY|EXPORT|IMPORT|ATTACH|DETACH|INSTALL|LOAD|VACUUM|CHECKPOINT)\b",
    re.IGNORECASE,
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sql", nargs="?", help="SQL query. If omitted, read from stdin.")
    parser.add_argument("--db", default="data/analytics.duckdb")
    parser.add_argument("--max-rows", type=int, default=200)
    args = parser.parse_args()

    sql = args.sql if args.sql is not None else sys.stdin.read()
    sql = sql.strip()

    if not sql:
        raise SystemExit("Empty SQL query")

    if BLOCKED.search(sql):
        raise SystemExit("Blocked: this helper is read-only and does not allow mutating SQL.")

    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"DuckDB file not found: {db}")

    con = duckdb.connect(str(db), read_only=True)
    try:
        rel = con.sql(sql)
        df = rel.limit(args.max_rows + 1).df()
    finally:
        con.close()

    truncated = len(df) > args.max_rows
    if truncated:
        df = df.iloc[:args.max_rows]

    if df.empty:
        print("(0 rows)")
    else:
        print(df.to_string(index=False))

    if truncated:
        print(f"\n[output truncated to {args.max_rows} rows]")

if __name__ == "__main__":
    main()
