#!/bin/bash
# macOS Finder launcher: double-click to stop the toolkit.
cd "$(dirname "$0")" || exit 1
./stop.sh
