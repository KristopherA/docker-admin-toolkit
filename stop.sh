#!/usr/bin/env bash
# Stop all toolkit containers. Data in named volumes is preserved.
set -euo pipefail
cd "$(dirname "$0")"
command -v docker >/dev/null || export PATH="/usr/local/bin:$HOME/.docker/bin:/opt/homebrew/bin:$PATH"
docker compose stop
echo "Toolkit stopped. Your data and settings are preserved."
