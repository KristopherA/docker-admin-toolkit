#!/usr/bin/env bash
# Create .env from .env.example with freshly generated secrets. Never overwrites an existing .env.
set -euo pipefail
cd "$(dirname "$0")"
gen_value() {
  case "$1" in
    SNIPEIT_APP_KEY) echo "base64:$(openssl rand -base64 32)" ;;
    NETBOX_SECRET_KEY|NETBOX_API_TOKEN_PEPPER) openssl rand -hex 32 ;;
    *) openssl rand -hex 24 ;;
  esac
}
if [[ -f .env ]]; then
  [[ -s .env && -n "$(tail -c1 .env)" ]] && echo >> .env
  # Append settings added to .env.example after this install; never touch existing values.
  added=()
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^([A-Z0-9_]+)= ]] || continue
    key=${BASH_REMATCH[1]}
    grep -q "^$key=" .env && continue
    if [[ "$line" == *=CHANGE_ME* ]]; then
      command -v openssl >/dev/null || { echo "OpenSSL is required to generate secrets."; exit 1; }
      line="$key=$(gen_value "$key")"
    fi
    printf '%s\n' "$line" >> .env
    added+=("$key")
  done < .env.example
  (( ${#added[@]} )) && echo "Added new settings to .env: ${added[*]}"
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
