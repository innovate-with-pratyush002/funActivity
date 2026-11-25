import unittest
from scripts.monitor_foreground import parse_foreground_package


class ForegroundParserTests(unittest.TestCase):
    def test_current_focus_window(self):
        output = 'mCurrentFocus=Window{be3a99c u0 com.android.settings/com.android.settings.Settings}'
        self.assertEqual(parse_foreground_package(output), 'com.android.settings')

    def test_focused_app_activity_record(self):
        output = 'mFocusedApp=ActivityRecord{200412484 u0 com.android.settings/.Settings t14}'
        self.assertEqual(parse_foreground_package(output), 'com.android.settings')

    def test_top_resumed_activity(self):
        output = 'topResumedActivity=ActivityRecord{200412484 u0 com.google.android.youtube/.HomeActivity t14}'
        self.assertEqual(parse_foreground_package(output), 'com.google.android.youtube')

    def test_unknown_when_no_focus_record(self):
        self.assertEqual(parse_foreground_package('no focus information'), 'unknown')


    def test_session_report_groups_sessions_and_counts_states(self):
        from scripts.session_report import summarize_rows

        rows = [
            ("session-a", "2026-11-25T10:00:00+05:30", "com.example.qa", 1),
            ("session-a", "2026-11-25T10:00:05+05:30", "com.android.launcher", 0),
            ("session-b", "2026-11-25T11:00:00+05:30", "unknown", 0),
        ]
        result = summarize_rows(rows)

        self.assertEqual(set(result), {"session-a", "session-b"})
        self.assertEqual(result["session-a"]["samples"], 2)
        self.assertEqual(result["session-a"]["target_foreground"], 1)
        self.assertEqual(result["session-a"]["other_foreground"], 1)
        self.assertEqual(result["session-a"]["first"], rows[0][1])
        self.assertEqual(result["session-a"]["last"], rows[1][1])
        self.assertEqual(result["session-b"]["other_foreground"], 1)

    def test_session_report_handles_empty_rows(self):
        from scripts.session_report import summarize_rows
        self.assertEqual(summarize_rows([]), {})



if __name__ == '__main__':
    unittest.main()