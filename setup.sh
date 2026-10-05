#!/usr/bin/env bash
# Create .env from .env.example with freshly generated secrets. Never overwrites an existing .env.
set -euo pipefail
cd "$(dirname "$0")"
if [[ -f .env ]]; then
  if grep -q 'CHANGE_ME' .env; then
    echo "Your .env still contains CHANGE_ME placeholders. Replace them, or move .env aside and run setup again."
    exit 1
  fi
  chmod 600 .env
  echo "Existing settings preserved."
  exit 0
fi
command -v openssl >/dev/null || { echo "OpenSSL is required to generate secrets."; exit 1; }
umask 077
temp_file=$(mktemp .env.tmp.XXXXXX)
trap 'rm -f "$temp_file"' EXIT
while IFS= read -r line || [[ -n "$line" ]]; do
  case "$line" in
    SNIPEIT_APP_KEY=CHANGE_ME*) line="SNIPEIT_APP_KEY=base64:$(openssl rand -base64 32)" ;;
    NETBOX_SECRET_KEY=CHANGE_ME*|NETBOX_API_TOKEN_PEPPER=CHANGE_ME*) line="${line%%=*}=$(openssl rand -hex 32)" ;;
    *=CHANGE_ME*) line="${line%%=*}=$(openssl rand -hex 24)" ;;
  esac
  printf '%s\n' "$line" >> "$temp_file"
done < .env.example
mv "$temp_file" .env
trap - EXIT
echo "Created private settings in .env. Back this file up; never regenerate it for an existing install."
