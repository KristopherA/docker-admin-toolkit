#!/bin/bash
# macOS Finder launcher: double-click to start the toolkit.
cd "$(dirname "$0")" || exit 1
if ! ./start.sh; then
  echo "Startup stopped. See the message above, then try again."
  read -r -p "Press Return to close… "
fi
