#!/bin/bash
# CocoIDE launcher for macOS — double-click this file in Finder.
# (A .command file opens Terminal and runs; we immediately close the
#  terminal window so you only see the IDE.)
cd "$(dirname "$0")"
python3 cocoideV1.91.pyw "$@" &
sleep 0.2
osascript -e 'tell application "Terminal" to close (every window whose name contains "CocoIDE.command")' >/dev/null 2>&1 &
wait
