# funActivity

A local, consent-based Android UI QA harness for a Google Play-enabled Android Emulator.

## Current milestone

- Uses a configurable target package. The current sample config names Truecaller only as an example.
- Checks that ADB can see a ready emulator/device.
- Captures timestamped screenshots only while the configured app is the foreground app.
- Stores capture metadata in a local SQLite database.
- Provides a command to inspect the local capture log.
- Does not upload screenshots or database records.

## Privacy boundary

Use only your own test account and testers who have explicitly agreed to the QA session. Capture is manually started and visible in the terminal. This project is not a hidden monitor and does not extract or profile other people's online, last-seen, or call activity. Do not collect personal information without each affected person's specific, informed consent.

## Prerequisites

- Ubuntu
- Python 3.10+
- Android SDK Platform Tools (adb)
- An Android Virtual Device created from a Google Play system image (Play Store included)

Android Studio is optional; command-line Android SDK tools can be used.

## Setup

1. Start your Google Play AVD.
2. Install the app from Play Store inside the emulator and sign in with a dedicated test account.
3. From the repository root, verify ADB:

    python3 scripts/check_adb.py

4. Open config/app.json and confirm target_package. The sample value is com.truecaller.
5. Start a manually initiated, authorized visible-screen QA session:

    python3 scripts/capture_visible_session.py --confirm-authorized-test-session

The default interval is 5 seconds. To override it, use --interval 10. Press Ctrl+C to stop.

## View captured records

    python3 scripts/show_log.py

Captures are stored locally under data/sessions/ and metadata in data/activity_log.sqlite3. The data/ directory is excluded from Git.

## Limitations

- A screenshot records only what is visible at that moment.
- Sampling every 5 seconds cannot establish exact event start/end times between screenshots.
- Screenshots may contain personal information. Keep them local, restrict access, and delete them when testing is complete.
- No app-specific OCR, personal-status extraction, or automated monitoring of other users is included.
