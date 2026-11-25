import unittest
from contextlib import closing
from scripts.import_consent_events import event_fingerprint, parse_timestamp


class EventImportTests(unittest.TestCase):
    def test_same_event_has_same_fingerprint(self):
        args = ("2026-11-25T10:00:00+05:30", "online", "demo-user-001", "consent-1", "demo")
        self.assertEqual(event_fingerprint(*args), event_fingerprint(*args))

    def test_source_app_is_part_of_fingerprint(self):
        args = ("2026-11-25T10:00:00+05:30", "online", "demo-user-001", "consent-1")
        self.assertNotEqual(event_fingerprint(*args, "app-a"), event_fingerprint(*args, "app-b"))

    def test_timestamp_requires_timezone(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2026-11-25T10:00:00")

    def test_timestamp_accepts_timezone(self):
        self.assertEqual(parse_timestamp("2026-11-25T10:00:00+05:30"), "2026-11-25T10:00:00+05:30")


    def test_schema_migration_backfills_and_removes_legacy_duplicates(self):
        import sqlite3
        from scripts.import_consent_events import ensure_schema

        with closing(sqlite3.connect(":memory:")) as db:
          with db:
              db.execute("""CREATE TABLE consented_activity_events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  event_at TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  subject_ref TEXT NOT NULL,
                  consent_record_id TEXT NOT NULL,
                  source_app TEXT NOT NULL,
                  imported_at TEXT NOT NULL
              )""")
              row = (
                  "2026-11-25T10:00:00+05:30", "online", "subject-1",
                  "consent-1", "demo", "2026-11-25T05:00:00+00:00"
              )
              db.execute("""INSERT INTO consented_activity_events
                  (event_at,event_type,subject_ref,consent_record_id,source_app,imported_at)
                  VALUES(?,?,?,?,?,?)""", row)
              db.execute("""INSERT INTO consented_activity_events
                  (event_at,event_type,subject_ref,consent_record_id,source_app,imported_at)
                  VALUES(?,?,?,?,?,?)""", row)

              ensure_schema(db)

              rows = db.execute(
                  "SELECT event_key FROM consented_activity_events"
              ).fetchall()
              self.assertEqual(len(rows), 1)
              self.assertTrue(rows[0][0])

              with self.assertRaises(sqlite3.IntegrityError):
                  db.execute("""INSERT INTO consented_activity_events
                      (event_at,event_type,subject_ref,consent_record_id,source_app,imported_at,event_key)
                      VALUES(?,?,?,?,?,?,?)""",
                      (*row[:5], row[5], rows[0][0]))



if __name__ == "__main__":
    unittest.main()
