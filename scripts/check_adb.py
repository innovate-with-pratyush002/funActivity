#!/usr/bin/env python3
"""Check ADB and list connected Android devices/emulators."""
import shutil
import subprocess
import sys


def main() -> int:
    adb = shutil.which("adb")
    if not adb:
        print("ERROR: adb was not found on PATH.")
        print("Install Android SDK Platform Tools, then add its platform-tools directory to PATH.")
        return 1
    result = subprocess.run([adb, "devices", "-l"], text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stderr.strip() or "ADB command failed.")
        return result.returncode
    print(result.stdout.strip())
    devices = [line for line in result.stdout.splitlines()[1:] if line.strip() and "\tdevice" in line]
    if not devices:
        print("\nNo ready device found. Start your Google Play AVD and run this command again.")
        return 2
    print(f"\nReady device(s): {len(devices)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
