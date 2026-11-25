"""Manually capture timestamped screenshots while an authorized test app is foregrounded."""
import argparse
import datetime as dt
import json
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

CONFIG_PATH = Path("config") / "app.json"


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {"target_package": "com.example.app", "capture_interval_seconds": 5}


def run_adb(serial, *args, binary=False):
    command = ["adb"]
    if serial:
        command += ["-s", serial]
    command += list(args)
    return subprocess.run(command, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=not binary).stdout


def foreground_package(serial):
    output = run_adb(serial, "shell", "dumpsys", "window", "windows")
    patterns = [
        r"mCurrentFocus=Window\{[^}]*\s([\w.]+)/",
        r"mFocusedApp=ActivityRecord\{[^}]*\s([\w.]+)/",
    ]
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return match.group(1)
    return None


def main():
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", default=config.get("target_package"),
                        help="Target package (defaults to config/app.json)")
    parser.add_argument("--interval", type=float, default=float(config.get("capture_interval_seconds", 5)),
                        help="Seconds between screenshots (minimum 2)")
    parser.add_argument("--serial", help="ADB device serial; omit when exactly one device is connected")
    parser.add_argument("--confirm-authorized-test-session", action="store_true",
                        help="Confirm a transparent QA session with your own test account/explicitly consenting testers")
    args = parser.parse_args()
    if not args.confirm_authorized_test_session:
        parser.error("A transparent, authorized test session must be explicitly confirmed.")
    if not args.package:
        parser.error("Set target_package in config/app.json or pass --package.")
    if args.interval < 2:
        parser.error("--interval must be at least 2 seconds.")

    devices_output = run_adb(None, "devices")
    devices = [line.split()[0] for line in devices_output.splitlines()[1:]
               if line.strip() and len(line.split()) > 1 and line.split()[1] == "device"]
    if args.serial:
        if args.serial not in devices:
            print(f"Device {args.serial!r} is not ready in ADB.", file=sys.stderr)
            return 2
        serial = args.serial
    elif len(devices) == 1:
        serial = devices[0]
    else:
        print(f"Expected exactly one ready device; found {len(devices)}. Use --serial.", file=sys.stderr)
        return 2

    session_id = dt.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    session_dir = Path("data") / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=False)
    db_path = Path("data") / "activity_log.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL, captured_at TEXT NOT NULL,
            device_serial TEXT NOT NULL, target_package TEXT NOT NULL,
            screenshot_path TEXT NOT NULL)""")
        db.commit()

    print(f"Session {session_id} started for {args.package}.")
    print("Only visible screenshots are recorded while the target app is foregrounded.")
    print("Press Ctrl+C to stop.")
    count = 0
    try:
        while True:
            current = foreground_package(serial)
            if current == args.package:
                timestamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
                image_path = session_dir / f"screen_{count:06d}.png"
                image_bytes = run_adb(serial, "exec-out", "screencap", "-p", binary=True)
                image_path.write_bytes(image_bytes)
                with sqlite3.connect(db_path) as db:
                    db.execute("INSERT INTO captures(session_id,captured_at,device_serial,target_package,screenshot_path) VALUES(?,?,?,?,?)",
                               (session_id, timestamp, serial, args.package, str(image_path)))
                    db.commit()
                count += 1
                print(f"[{timestamp}] captured {image_path}")
            else:
                print(f"Target app is not foreground (current: {current or 'unknown'}); skipped.")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\nSession stopped. Saved {count} screenshot(s) to {session_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
