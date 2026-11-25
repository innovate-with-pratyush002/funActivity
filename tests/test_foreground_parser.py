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


if __name__ == '__main__':
    unittest.main()