#!/usr/bin/env python3
"""Summarize foreground observations without inspecting app content."""
import argparse
import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "activity_log.sqlite3"


def summarize_rows(rows):
    """Group ordered DB rows by session without estimating elapsed durations."""
    sessions = {}
    for session_id, stamp, foreground, active in rows:
        item = sessions.setdefault(session_id, {
            "first": stamp, "last": stamp, "samples": 0,
            "target_foreground": 0, "other_foreground": 0,
            "transitions": []
        })
        item["last"] = stamp
        item["samples"] += 1
        item["target_foreground" if active else "other_foreground"] += 1
        item["transitions"].append((stamp, foreground, bool(active)))
    return sessions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", help="Optional session ID")
    args = parser.parse_args()
    if not DB_PATH.exists():
        print("No monitoring database found.")
        return 0

    query = """SELECT session_id, observed_at, foreground_package,
                      target_is_foreground
               FROM foreground_observations"""
    params = ()
    if args.session:
        query += " WHERE session_id = ?"
        params = (args.session,)
    query += " ORDER BY id"

    with sqlite3.connect(DB_PATH) as db:
        table = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='foreground_observations'"
        ).fetchone()
        if not table:
            print("No foreground monitoring records yet.")
            return 0
        rows = db.execute(query, params).fetchall()

    if not rows:
        print("No matching foreground observations.")
        return 0

    sessions = summarize_rows(rows)
    for session_id, item in sessions.items():
        print(f"\nSession: {session_id}")
        print(f"First observation: {item['first']}")
        print(f"Last observation:  {item['last']}")
        print(f"State transitions: {item['samples']}")
        print(f"Target foreground: {item['target_foreground']}")
        print(f"Other/unknown foreground: {item['other_foreground']}")
        print("Transitions:")
        for stamp, package, active in item["transitions"]:
            print(f"  {stamp} | {package} | target_active={active}")
    print("\nNote: counts are state transitions, not exact duration or user online status.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
