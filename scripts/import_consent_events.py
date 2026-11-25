#!/usr/bin/env python3
"""Import first-party activity events exported by an app backend for opted-in testers.

Input is newline-delimited JSON (JSONL). This tool does not scrape screens,
read notifications, or infer another app's private activity.
"""
import argparse
import datetime as dt
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl_file", help="JSONL export from your own app's backend")
    parser.add_argument("--source-app", required=True, help="Your app identifier/name")
    args = parser.parse_args()

    source = Path(args.jsonl_file)
    if not source.is_file():
        parser.error(f"Input file not found: {source}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    imported = 0
    rejected = 0

    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS consented_activity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            subject_ref TEXT NOT NULL,
            consent_record_id TEXT NOT NULL,
            source_app TEXT NOT NULL,
            imported_at TEXT NOT NULL
        )""")

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
                    imported_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
                    db.execute(
                        """INSERT INTO consented_activity_events
                        (event_at,event_type,subject_ref,consent_record_id,source_app,imported_at)
                        VALUES(?,?,?,?,?,?)""",
                        (event_at, event_type, subject_ref, consent_ref, args.source_app, imported_at),
                    )
                    imported += 1
                except (json.JSONDecodeError, ValueError, KeyError) as exc:
                    rejected += 1
                    print(f"Line {line_number}: rejected: {exc}", file=sys.stderr)
        db.commit()

    print(f"Imported: {imported}")
    print(f"Rejected: {rejected}")
    print(f"Database: {DB_PATH}")
    return 0 if rejected == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
