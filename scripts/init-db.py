#!/usr/bin/env python3
"""
init-db.py — Initialize the local SQLite database from schema/schema.sql
Part of proline-claw (https://github.com/roofclaw/proline-claw)

Idempotent. Creates data/proline.db with all 15 tables and their indexes.
Safe to run more than once — CREATE TABLE IF NOT EXISTS means existing data
is preserved.

Usage:
    python3 scripts/init-db.py
"""

import os
import sqlite3
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCHEMA_PATH = os.path.join(REPO_ROOT, "schema", "schema.sql")
DB_PATH = os.path.join(REPO_ROOT, "data", "proline.db")


def main():
    if not os.path.exists(SCHEMA_PATH):
        print(f"Error: schema file not found at {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    existed = os.path.exists(DB_PATH)

    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    db = sqlite3.connect(DB_PATH)
    try:
        db.executescript(schema_sql)
        db.commit()
    finally:
        db.close()

    tables = sqlite3.connect(DB_PATH).execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()

    action = "Updated" if existed else "Created"
    print(f"{action} {DB_PATH}")
    print(f"Tables ({len(tables)}): {', '.join(t[0] for t in tables)}")
    if not existed:
        print()
        print("Next: put your ProLine credentials in .env, then run:")
        print("  python3 scripts/onboard.py")


if __name__ == "__main__":
    main()
