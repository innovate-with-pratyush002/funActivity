#!/usr/bin/env python3
"""Import consented first-party JSONL events into SQLite idempotently."""
import argparse
import datetime as dt
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("data") / "activity_log.sqlite3"
ALLOWED_EVENTS = {"online", "offline", "call_started", "call_ended", "last_active"}
REQUIRED = {"event_at", "event_type", "subject_ref", "consent_record_id"}


def parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("event_at must be an ISO-8601 string")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("event_at must include a timezone")
    return parsed.isoformat(timespec="seconds")


def event_fingerprint(event_at, event_type, subject_ref, consent_ref, source_app):
    stable = "\\x1f".join((event_at, event_type, subject_ref, consent_ref, source_app))
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def ensure_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS consented_activity_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_at TEXT NOT NULL,
        event_type TEXT NOT NULL,
        subject_ref TEXT NOT NULL,
        consent_record_id TEXT NOT NULL,
        source_app TEXT NOT NULL,
        imported_at TEXT NOT NULL,
        event_key TEXT
    )""")
    columns = {row[1] for row in db.execute("PRAGMA table_info(consented_activity_events)")}
    if "event_key" not in columns:
        db.execute("ALTER TABLE consented_activity_events ADD COLUMN event_key TEXT")

    # Backfill older rows and remove duplicates created by earlier non-idempotent imports.
    rows = db.execute("""SELECT id,event_at,event_type,subject_ref,consent_record_id,source_app
                         FROM consented_activity_events WHERE event_key IS NULL""").fetchall()
    for row in rows:
        key = event_fingerprint(*row[1:])
        db.execute("UPDATE consented_activity_events SET event_key=? WHERE id=?", (key, row[0]))
    db.execute("""DELETE FROM consented_activity_events
                  WHERE id NOT IN (
                    SELECT MIN(id) FROM consented_activity_events GROUP BY event_key
                  )""")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_event_key ON consented_activity_events(event_key)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl_file", help="JSONL export from an authorized first-party source")
    parser.add_argument("--source-app", required=True, help="Source app identifier/name")
    args = parser.parse_args()

    source = Path(args.jsonl_file)
    if not source.is_file():
        parser.error(f"Input file not found: {source}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    imported = rejected = duplicates = 0
    with sqlite3.connect(DB_PATH) as db:
        ensure_schema(db)
        with source.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        raise ValueError("each JSONL line must be an object")
                    missing = REQUIRED - event.keys()
                    if missing:
                        raise ValueError("missing fields: " + ", ".join(sorted(missing)))
                    if event.get("consent_granted") is not True:
                        raise ValueError("consent_granted must be true")
                    event_type = event["event_type"]
                    if event_type not in ALLOWED_EVENTS:
                        raise ValueError("unsupported event_type")
                    subject_ref = event["subject_ref"]
                    consent_ref = event["consent_record_id"]
                    if not isinstance(subject_ref, str) or not subject_ref.strip():
                        raise ValueError("subject_ref must be a non-empty pseudonymous reference")
                    if not isinstance(consent_ref, str) or not consent_ref.strip():
                        raise ValueError("consent_record_id must be a non-empty reference")
                    event_at = parse_timestamp(event["event_at"])
                    key = event_fingerprint(event_at, event_type, subject_ref, consent_ref, args.source_app)
                    imported_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
                    cursor = db.execute(
                        """INSERT OR IGNORE INTO consented_activity_events
                        (event_at,event_type,subject_ref,consent_record_id,source_app,imported_at,event_key)
                        VALUES(?,?,?,?,?,?,?)""",
                        (event_at, event_type, subject_ref, consent_ref, args.source_app, imported_at, key),
                    )
                    if cursor.rowcount:
                        imported += 1
                    else:
                        duplicates += 1
                except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
                    rejected += 1
                    print(f"Line {line_number}: rejected: {exc}", file=sys.stderr)
        db.commit()

    print(f"Imported: {imported}")
    print(f"Duplicates skipped: {duplicates}")
    print(f"Rejected: {rejected}")
    print(f"Database: {DB_PATH}")
    return 0 if rejected == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
