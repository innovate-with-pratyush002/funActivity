# funActivity

A local, consent-based Android UI QA harness for a Google Play-enabled Android Emulator, plus an importer for first-party activity events exported by your own app backend.

## Current capabilities

- Checks ADB connectivity and lists ready Android devices.
- Checks whether the configured QA app package is installed.
- Captures timestamped screenshots only while the configured app is foregrounded; capture is manually started and visible in the terminal.
- Stores screenshot metadata locally in SQLite.
- Imports first-party activity events from a JSONL export, requiring an explicit consent flag and a consent-record reference on every event.
- Displays locally imported events, optionally filtered by pseudonymous subject reference.
- Does not upload screenshots or database records.

## Privacy and data boundary

Use only your own test account and testers who have explicitly opted in to the specific data collection. This project does not scrape another app's private UI, notifications, online/last-seen indicators, or call activity, and does not infer private activity from screenshots. Activity-event import is intended for events emitted by your own app backend under its own consent and access controls. Keep identifiers pseudonymous and avoid importing phone numbers, contact lists, or unnecessary personal data.

## Prerequisites

- Ubuntu
- Python 3.10+
- Android SDK Platform Tools (adb)
- An Android Virtual Device created from a Google Play system image

Android Studio is optional; Android SDK command-line tools are sufficient.

## Setup

1. Start your Google Play AVD.
2. Install your own QA build in the emulator and sign in with a dedicated test account.
3. From the repository root, verify ADB:

    python3 scripts/check_adb.py

4. Check the configured package in config/app.json:

    python3 scripts/check_target_app.py

5. Start a manually initiated, visible QA screenshot session:

    python3 scripts/capture_visible_session.py --confirm-authorized-test-session

The default screenshot interval is 5 seconds. To override it, use --interval 10. Press Ctrl+C to stop.

## First-party event import

Your own app backend can export one JSON object per line. Required fields:

- event_at: ISO-8601 timestamp including timezone
- event_type: one of online, offline, call_started, call_ended, last_active
- subject_ref: pseudonymous user reference
- consent_record_id: reference to the consent record
- consent_granted: must be boolean true

A synthetic sample is included at samples/demo_events.jsonl. Import it to smoke-test the database:

    python3 scripts/import_consent_events.py samples/demo_events.jsonl --source-app demo

View imported events:

    python3 scripts/show_events.py

Filter by pseudonymous subject:

    python3 scripts/show_events.py --subject demo-user-001

The importer validates the event shape and consent flag; it cannot independently prove that the source app obtained valid consent. Your backend must enforce consent, authorization, retention, and revocation before exporting events.

## View screenshot records

    python3 scripts/show_log.py

Screenshots are stored under data/sessions/; SQLite metadata is stored in data/activity_log.sqlite3. The data/ directory is excluded from Git.

## Current limitations

- Screenshot capture records only visible pixels while the app is foregrounded.
- Screenshot sampling cannot establish exact event start/end times.
- The event importer accepts backend-exported events; a production backend/API integration is not included yet.
- No app-specific OCR or extraction of third-party personal activity is included.
- Screenshots may contain personal information. Keep them local, restrict access, and delete them when testing is complete.

## Foreground session monitoring

For an authorized QA session, you can record when the configured app becomes or stops being the emulator's foreground app. This stores only timestamps, package names, and a foreground boolean; it does not read screen contents, notifications, contacts, call state, or private activity indicators.

Start monitoring (from the repository root):

    python3 scripts/monitor_foreground.py --confirm-authorized-test-session

Optional flags:

    python3 scripts/monitor_foreground.py --confirm-authorized-test-session --interval 3
    python3 scripts/monitor_foreground.py --confirm-authorized-test-session --duration 300
    python3 scripts/monitor_foreground.py --confirm-authorized-test-session --serial emulator-5554

Generate a report:

    python3 scripts/session_report.py
    python3 scripts/session_report.py --session 20261125_153000

The report shows foreground state transitions. It does not claim that a person is online/offline in the target service, and transition counts are not exact usage durations.
