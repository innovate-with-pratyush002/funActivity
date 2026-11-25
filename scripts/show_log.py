"""Print locally stored screenshot observations from the SQLite log."""
import argparse
import sqlite3
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", help="Optional session ID to filter")
    args = parser.parse_args()
    db_path = Path("data") / "activity_log.sqlite3"
    if not db_path.exists():
        print("No capture database found yet. Start a visible QA capture session first.")
        return 0
    query = """SELECT captured_at, device_serial, target_package, screenshot_path
               FROM captures"""
    params = ()
    if args.session:
        query += " WHERE session_id = ?"
        params = (args.session,)
    query += " ORDER BY id"
    with sqlite3.connect(db_path) as db:
        rows = db.execute(query, params).fetchall()
    if not rows:
        print("No matching captures found.")
        return 0
    print("Captured at | Device | Package | Screenshot")
    for row in rows:
        print(" | ".join(str(value) for value in row))
    print(f"\nTotal captures: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
