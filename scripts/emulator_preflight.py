#!/usr/bin/env python3
"""Run non-invasive readiness checks for the Android emulator."""
import argparse
import shutil
import subprocess
import sys


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"Command failed: {' '.join(command)}")
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', help='ADB serial; required when multiple devices are connected')
    args = parser.parse_args()
    if not shutil.which('adb'):
        print('FAIL: adb is not installed or not on PATH.')
        return 1
    try:
        lines = run(['adb', 'devices']).splitlines()[1:]
        devices = [line.split()[0] for line in lines if len(line.split()) >= 2 and line.split()[1] == 'device']
        if args.serial:
            if args.serial not in devices:
                raise RuntimeError(f'{args.serial} is not a ready ADB device')
            serial = args.serial
        elif len(devices) == 1:
            serial = devices[0]
        else:
            raise RuntimeError(f'Expected exactly one ready device; found {len(devices)}. Pass --serial.')
        def adb(*parts):
            return run(['adb', '-s', serial, *parts])
        boot = adb('shell', 'getprop', 'sys.boot_completed')
        android = adb('shell', 'getprop', 'ro.build.version.release')
        sdk = adb('shell', 'getprop', 'ro.build.version.sdk')
        size = adb('shell', 'wm', 'size')
        density = adb('shell', 'wm', 'density')
        foreground = adb('shell', 'dumpsys', 'window', 'windows')
        from monitor_foreground import parse_foreground_package
        package = parse_foreground_package(foreground)
        if package == 'unknown':
            activity = adb('shell', 'dumpsys', 'activity', 'activities')
            package = parse_foreground_package(activity)
        third_party = adb('shell', 'pm', 'list', 'packages', '-3').splitlines()
        print('EMULATOR PREFLIGHT')
        print(f'Device: {serial}')
        print(f'Boot completed: {boot == "1"} (value={boot or "empty"})')
        print(f'Android: {android} (API {sdk})')
        print(f'Display: {size}; {density}')
        print(f'Foreground package: {package}')
        print(f'User-installed package count: {len(third_party)}')
        for item in third_party:
            print(f'  {item.removeprefix("package:")}')
        return 0 if boot == '1' else 2
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())