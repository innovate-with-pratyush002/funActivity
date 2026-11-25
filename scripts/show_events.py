#!/usr/bin/env python3
"""Display consented first-party activity events stored in the local SQLite database."""
import argparse
import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "activity_log.sqlite3"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", help="Filter by pseudonymous subject reference")
    parser.add_argument("--limit", type=int, default=100, help="Maximum rows (default: 100)")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    if not DB_PATH.exists():
        print("No local event database found yet.")
        return 0

    query = """SELECT event_at,event_type,subject_ref,consent_record_id,source_app
               FROM consented_activity_events"""
    params = []
    if args.subject:
        query += " WHERE subject_ref = ?"
        params.append(args.subject)
    query += " ORDER BY event_at DESC LIMIT ?"
    params.append(args.limit)

    with sqlite3.connect(DB_PATH) as db:
        table = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='consented_activity_events'"
        ).fetchone()
        if not table:
            print("No consented activity events have been imported yet.")
            return 0
        rows = db.execute(query, params).fetchall()

    if not rows:
        print("No matching events found.")
        return 0
    print("Event time | Event | Subject ref | Consent ref | Source app")
    for row in rows:
        print(" | ".join(str(value) for value in row))
    print(f"\nDisplayed: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
