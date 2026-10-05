#!/usr/bin/env bash
# Start the toolkit on Linux or macOS. Usage: ./start.sh [--no-browser]
set -euo pipefail
cd "$(dirname "$0")"
open_browser=true
[[ "${1:-}" == "--no-browser" ]] && open_browser=false

# Docker Desktop on macOS may not be on PATH when launched from Finder.
command -v docker >/dev/null || export PATH="/usr/local/bin:$HOME/.docker/bin:/opt/homebrew/bin:$PATH"
command -v docker >/dev/null || { echo "Docker is not installed: https://docs.docker.com/get-docker/"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "The Docker Compose plugin is required."; exit 1; }

if ! docker info >/dev/null 2>&1; then
  if [[ "$(uname -s)" == "Darwin" ]]; then
    echo "Starting Docker Desktop…"
    open -a Docker
    for ((i=0; i<60; i++)); do docker info >/dev/null 2>&1 && break; sleep 2; done
  fi
  docker info >/dev/null 2>&1 || { echo "Docker is not running (or you lack permission to use it)."; exit 1; }
fi

./setup.sh
env_get() { sed -n "s/^$1=//p" .env | tail -1; }

compose=(docker compose -f compose.yml)
proxy_enabled=$(env_get PROXY_ENABLED)
domain=$(env_get TOOLKIT_DOMAIN)
if [[ "$proxy_enabled" == "true" ]]; then
  network=$(env_get PROXY_NETWORK); network=${network:-proxy}
  docker network inspect "$network" >/dev/null 2>&1 || docker network create "$network" >/dev/null
  compose+=(-f compose.proxy.yml)
fi

"${compose[@]}" config --quiet
echo "Starting the toolkit. The first run downloads images and can take several minutes."
"${compose[@]}" up -d --build

port=$("${compose[@]}" port dashboard 8080); port=${port##*:}
for ((i=0; i<30; i++)); do
  curl --silent --fail --max-time 2 "http://127.0.0.1:$port/api/health" >/dev/null && break
  sleep 2
done
curl --silent --fail --max-time 2 "http://127.0.0.1:$port/api/health" >/dev/null \
  || { echo "The dashboard did not become ready. Check: docker compose logs dashboard"; exit 1; }

link_host=$(env_get LINK_HOST); link_host=${link_host:-localhost}
url="http://$link_host:$port"
[[ "$proxy_enabled" == "true" && -n "$domain" ]] && url="https://toolkit.$domain"
echo "Dashboard: $url  (local fallback: http://localhost:$port)"
echo "Some applications may still be initializing; the dashboard shows their availability."

if $open_browser; then
  if command -v open >/dev/null && [[ "$(uname -s)" == "Darwin" ]]; then open "$url"
  elif command -v xdg-open >/dev/null && [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then xdg-open "$url" >/dev/null 2>&1 &
  fi
fi
