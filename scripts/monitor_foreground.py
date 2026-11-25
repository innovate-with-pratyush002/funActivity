#!/usr/bin/env python3
"""Record only whether the configured QA app is the foreground app on an emulator.

This intentionally does not inspect screen text, notifications, contacts, call state,
or another app's private data.
"""
import argparse
import datetime as dt
import json
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

CONFIG = Path("config") / "app.json"
DB_PATH = Path("data") / "activity_log.sqlite3"


def adb(serial, *args):
    result = subprocess.run(
        ["adb", "-s", serial, *args], capture_output=True, text=True
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "ADB command failed")
    return result.stdout


def foreground_package(serial):
    output = adb(serial, "shell", "dumpsys", "window", "windows")
    patterns = (
        r"mCurrentFocus=Window\{[^}]*\s([\w.]+)/",
        r"mFocusedApp=ActivityRecord\{[^}]*\s([\w.]+)/",
    )
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return match.group(1)
    return "unknown"


def choose_device(requested):
    output = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True).stdout
    devices = [line.split()[0] for line in output.splitlines()[1:]
               if len(line.split()) >= 2 and line.split()[1] == "device"]
    if requested:
        if requested not in devices:
            raise RuntimeError(f"Device {requested} is not ready")
        return requested
    if len(devices) != 1:
        raise RuntimeError(f"Expected one ready device, found {len(devices)}; pass --serial")
    return devices[0]


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", default=config.get("target_package"))
    parser.add_argument("--serial")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--duration", type=int, default=0,
                        help="Stop after N seconds; 0 means until Ctrl+C")
    parser.add_argument("--confirm-authorized-test-session", action="store_true")
    args = parser.parse_args()
    if not args.confirm_authorized_test_session:
        parser.error("Confirm that this is your own QA session or an explicitly authorized test.")
    if not args.package or args.interval < 1 or args.duration < 0:
        parser.error("Provide a package, interval >= 1 second, and duration >= 0.")

    try:
        serial = choose_device(args.serial)
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        session_id = dt.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
        with sqlite3.connect(DB_PATH) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS foreground_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                device_serial TEXT NOT NULL,
                target_package TEXT NOT NULL,
                foreground_package TEXT NOT NULL,
                target_is_foreground INTEGER NOT NULL
            )""")
            db.commit()

        print(f"Monitoring foreground status for {args.package} on {serial}.")
        print("Only package name + timestamp + foreground boolean are recorded.")
        print("No screen contents, notifications, contacts, or call information are read.")
        print("Press Ctrl+C to stop.")
        started = time.monotonic()
        last_state = None
        try:
            while not args.duration or time.monotonic() - started < args.duration:
                current = foreground_package(serial)
                is_target = current == args.package
                state = (current, is_target)
                if state != last_state:
                    stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
                    with sqlite3.connect(DB_PATH) as db:
                        db.execute("""INSERT INTO foreground_observations
                            (session_id, observed_at, device_serial, target_package,
                             foreground_package, target_is_foreground)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                            (session_id, stamp, serial, args.package, current, int(is_target)))
                        db.commit()
                    print(f"[{stamp}] foreground={current}; target_active={is_target}")
                    last_state = state
                time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
        print(f"Session stopped: {session_id}")
        print("Run: python3 scripts/session_report.py")
        return 0
    except (OSError, json.JSONDecodeError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
