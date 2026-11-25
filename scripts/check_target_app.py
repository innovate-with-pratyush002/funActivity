#!/usr/bin/env python3
"""Check whether the configured QA app is installed on the connected emulator."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

CONFIG = Path("config") / "app.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", help="Override package from config/app.json")
    parser.add_argument("--serial", help="ADB serial; required if multiple devices are connected")
    args = parser.parse_args()

    if not shutil.which("adb"):
        print("ERROR: adb not found on PATH.", file=sys.stderr)
        return 1
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {CONFIG}: {exc}", file=sys.stderr)
        return 1

    package = args.package or config.get("target_package")
    if not isinstance(package, str) or not package.strip():
        print("ERROR: target_package is missing in config/app.json.", file=sys.stderr)
        return 1

    devices_result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    devices = [line.split()[0] for line in devices_result.stdout.splitlines()[1:]
               if len(line.split()) >= 2 and line.split()[1] == "device"]
    if args.serial:
        if args.serial not in devices:
            print(f"ERROR: device {args.serial} is not ready.")
            return 2
        serial = args.serial
    elif len(devices) == 1:
        serial = devices[0]
    else:
        print(f"ERROR: expected one ready device, found {len(devices)}. Use --serial.")
        return 2

    result = subprocess.run(["adb", "-s", serial, "shell", "pm", "path", package],
                            capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        print(f"NOT INSTALLED: {package} on {serial}")
        print("Install your own QA build in the emulator, or pass the correct --package.")
        return 3

    print(f"INSTALLED: {package}")
    print(f"DEVICE: {serial}")
    print(result.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
