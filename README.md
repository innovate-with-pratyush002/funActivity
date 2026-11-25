# funActivity

A local, consent-based Android QA harness for testing one app inside a Google Play-enabled Android Emulator.

## Scope and privacy

This project is for controlled testing with your own test account and testers who have explicitly agreed to the test. It captures only while the selected app is foregrounded, only after you manually start a session, and stores data locally. It is not a hidden monitor and must not be used to build profiles of unrelated people or collect call/availability metadata without their specific informed consent.

The first milestone verifies ADB connectivity and records timestamped screenshots plus foreground-package metadata. App-specific OCR and parsing are not enabled until the target package and exact test-screen fields are confirmed.

## Prerequisites

- Ubuntu
- Python 3.10+
- Android SDK Platform Tools (adb)
- An Android Virtual Device created from a Google Play system image (Play Store included)

Android Studio is optional; Android SDK command-line tools and the emulator package can be installed separately.

## Quick start

1. Create/start a Google Play AVD and install your app from Play Store inside that emulator.
2. In the emulator, sign in using a dedicated test account.
3. Run:

    python3 scripts/check_adb.py

4. Start a visible, manually initiated capture session. Replace the package name with your app's Android package ID:

    python3 scripts/capture_visible_session.py --package com.example.app --interval 5 --confirm-authorized-test-session

Press Ctrl+C to stop. Screenshots and a SQLite session log are saved under data/ and are not uploaded.

## Current limitations

- The tool records only what is visibly rendered in the emulator; it cannot see hidden app state or prove exact event times between samples.
- Screen changes, scrolling, pagination, network latency, and emulator sleep can affect observations.
- This QA starter does not automate extraction of other users' presence, last-seen, or call metadata.
