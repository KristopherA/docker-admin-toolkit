# Sources and compatibility

Registry manifests checked on 2026-10-04 support both Linux ARM64 and AMD64 for:

- `ghcr.io/corentinth/it-tools:latest` — https://github.com/CorentinTh/it-tools
- `ghcr.io/gchq/cyberchef:latest` — https://github.com/gchq/CyberChef
- `louislam/uptime-kuma:2` — https://github.com/louislam/uptime-kuma
- `ghcr.io/twin/gatus:stable` — https://github.com/TwiN/gatus
- `netboxcommunity/netbox:v4.7-5.1.1` — https://github.com/netbox-community/netbox-docker
- `snipe/snipe-it:v8.7.0` — https://github.com/grokability/snipe-it
- `ghcr.io/dougburks/so-crates:main` — https://so-crates.org/installation/docker/ (ALLOWED_HOSTS required behind a reverse proxy)
- `postgres:18-alpine`, `valkey/valkey:9.1-alpine`, and `mariadb:11.4.7` — their upstream container distributions.

Stirling-PDF's original `stirlingtools/stirling-pdf:3.0.1` tag returned not found. Docker Hub's `stirlingtools/stirling-pdf:latest` was verified with both architectures and pinned by its image index digest:

`sha256:c195925341aa35ee5932d9c225edef48a92e46a1280963180d79619cb5f29e6e`

Authentication variables follow https://docs.stirlingpdf.com/Configuration/Security/System%20and%20Security/. The ambiguous `DISABLE_ADDITIONAL_FEATURES` flag was removed; explicit login configuration remains enabled. Current upstream installation documentation uses the `docker.stirlingpdf.com` registry; this adaptation keeps the directly verified Docker Hub distribution pinned to a digest.

Docker Engine install: https://docs.docker.com/engine/install/
Docker Desktop (macOS/Windows): https://docs.docker.com/desktop/
