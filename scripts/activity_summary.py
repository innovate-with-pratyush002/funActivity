#!/usr/bin/env python3
"""Summarize first-party activity events already imported into the local SQLite database."""
import argparse
import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "activity_log.sqlite3"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", help="Filter by pseudonymous subject reference")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print("No local event database found yet. Import an authorized backend export first.")
        return 0

    with sqlite3.connect(DB_PATH) as db:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='consented_activity_events'"
        ).fetchone()
        if not exists:
            print("No consented activity events have been imported yet.")
            return 0

        where = " WHERE subject_ref = ?" if args.subject else ""
        params = (args.subject,) if args.subject else ()
        rows = db.execute(
            """SELECT subject_ref, event_type, COUNT(*), MIN(event_at), MAX(event_at)
               FROM consented_activity_events""" + where +
            " GROUP BY subject_ref, event_type ORDER BY subject_ref, event_type",
            params,
        ).fetchall()

        totals = db.execute(
            "SELECT COUNT(*), COUNT(DISTINCT subject_ref) FROM consented_activity_events" + where,
            params,
        ).fetchone()

    if not rows:
        print("No matching events found.")
        return 0

    print(f"Events: {totals[0]} | Pseudonymous subjects: {totals[1]}")
    print("Subject ref | Event type | Count | First observed | Last observed")
    for row in rows:
        print(" | ".join(str(value) for value in row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
