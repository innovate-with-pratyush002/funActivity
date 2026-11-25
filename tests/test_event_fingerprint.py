import unittest
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


if __name__ == "__main__":
    unittest.main()
