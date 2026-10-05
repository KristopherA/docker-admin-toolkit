# Docker Admin Toolkit

Ten self-hosted admin and security tools plus a lightweight dashboard, started together with one Docker Compose project. Runs on Linux, macOS (Docker Desktop), and Windows (Docker Desktop/WSL2), on ARM64 and AMD64.

By default every web port binds to **127.0.0.1**; databases and caches publish no ports and nothing mounts the Docker socket.

| Service | Default address | Purpose | First-run setup |
|---|---|---|---|
| Dashboard | http://localhost:8080 | Launcher + availability checks | None |
| IT-Tools | http://localhost:8081 | Encoders, converters, calculators | None |
| CyberChef | http://localhost:8082 | Data decoding/transform recipes | None |
| Uptime Kuma | http://localhost:3001 | Uptime monitoring | Create admin in web wizard |
| Stirling-PDF | http://localhost:8083 | PDF merge/split/OCR | `admin` / `STIRLING_ADMIN_PASSWORD` from `.env` |
| Gatus | http://localhost:8084 | Health checks (pre-configured for the toolkit) | None |
| NetBox | http://localhost:8000 | IPAM / DCIM | `createsuperuser` (below) |
| Snipe-IT | http://localhost:8001 | Asset inventory | Web setup wizard |
| SO-CRATES | http://localhost:8085 | PCAP/binary/log analysis (Suricata, YARA, Sigma) | None |
| ConvertX | http://localhost:8087 | File conversion (images, audio, video, ebooks, docs) | Create account on first visit |
| MyIP | http://localhost:8088 | Public IP, DNS/WebRTC leak, connectivity, whois | None |

The dashboard also links (without proxying or probing) to 13 public sandbox and URL-reputation sites. Edit `LINKS` in `dashboard/server.py` to change them. Public sandboxes may publish submissions; never upload confidential files.

## Quick start

Requirements: Docker Engine 24+ with the Compose plugin (or Docker Desktop), OpenSSL, and roughly 8 GB RAM / 4 CPUs available to Docker.

```bash
git clone https://github.com/KristopherA/docker-admin-toolkit.git
cd docker-admin-toolkit
./start.sh                # generates .env, starts everything, opens the dashboard
```

macOS users can double-click `start.command` / `stop.command` in Finder instead.

Manual equivalent:

```bash
./setup.sh                # creates .env with unique secrets; on later runs only appends new settings
docker compose up -d --build
```

First start downloads images and runs migrations; allow several minutes. Then create the NetBox admin once:

```bash
docker compose exec netbox /opt/netbox/netbox/manage.py createsuperuser
```

Tool notes:

- **ConvertX** — registration is disabled after the first account; create it right away. Its login cookie requires localhost or HTTPS, so set `CONVERTX_HTTP_ALLOWED=true` only for plain-HTTP LAN access. Converted files are deleted after `CONVERTX_AUTO_DELETE_HOURS`.
- **MyIP** — the page calls third-party IP/geolocation services from your browser. Its API only answers referers listed in `ALLOWED_DOMAINS` (set automatically from `LINK_HOST` and the proxy domain). Without MaxMind GeoLite2 credentials (`MYIP_MAXMIND_*`, free account) its local geolocation endpoint returns errors; other checks still work. More optional keys: see the [MyIP env reference](https://docs.ipcheck.ing/developer/reference/environment-variables).

## Configuration (`.env`)

| Variable | Default | Notes |
|---|---|---|
| `BIND_ADDRESS` | `127.0.0.1` | Set `0.0.0.0` to expose on the LAN (add a firewall) |
| `LINK_HOST` | `localhost` | Hostname the dashboard puts in tool links, e.g. the server's DNS name |
| `TIME_ZONE` | `UTC` | e.g. `America/New_York` |
| `*_PORT` | see table | Change if a port is taken, then `docker compose up -d` |
| `*_TAG` / `STIRLING_PDF_IMAGE` | pinned/channel | Image versions |
| `PROXY_ENABLED` | `false` | Enable HTTPS hostnames (next section) |

`.env` holds generated secrets, is created with mode `0600`, and is git-ignored. After pulling toolkit updates, `./setup.sh` (or `./start.sh`) appends any newly introduced settings, generating secrets where needed, and never changes existing values. Back it up — the Snipe-IT `APP_KEY` encrypts data and must not change.

## Optional: HTTPS via a reverse proxy

`compose.proxy.yml` attaches each web service to an external Docker network with stable aliases (`toolkit-dashboard`, `toolkit-netbox`, ...) so any proxy on that network (Caddy, Traefik, nginx) can route `<name>.${TOOLKIT_DOMAIN}` to it. It also switches NetBox CSRF origins, SO-CRATES allowed hosts, and Snipe-IT to HTTPS with secure cookies.

1. In `.env`: `PROXY_ENABLED=true`, `TOOLKIT_DOMAIN=tools.example.com`, `PROXY_NETWORK=proxy`.
2. Set `PROXY_TRUSTED_SUBNET` to the network's subnet: `docker network inspect proxy -f '{{(index .IPAM.Config 0).Subnet}}'`.
3. Add routes to your proxy — `proxy/Caddyfile.example` has a ready-made Caddy config.
4. Point DNS (or `/etc/hosts`) for `toolkit`, `it-tools`, `cyberchef`, `uptime`, `pdf`, `gatus`, `netbox`, `snipeit`, `socrates`, `convertx`, `myip` `.${TOOLKIT_DOMAIN}` at the proxy.
5. `./start.sh` (creates the network if missing, includes the override automatically, and lists any hostnames that do not resolve).

Manual: `docker compose -f compose.yml -f compose.proxy.yml up -d`

## Operations

```bash
docker compose ps                     # status
docker compose logs --tail=100 netbox # one service's logs
./stop.sh                             # stop, keep data
docker compose down                   # remove containers, keep volumes
docker compose down --volumes         # DELETES ALL DATA
```

The dashboard probes each service every 15 s from inside its container. A redirect or auth response counts as "responding"; this confirms the web service answers, not that every feature works.

## Backups and upgrades

Back up `.env`, `config/`, the databases, and named volumes before upgrading.

```bash
mkdir -p backups && chmod 700 backups
docker compose exec -T netbox-postgres pg_dump -U netbox netbox > backups/netbox.sql
docker compose exec -T snipe-db sh -c 'mariadb-dump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' > backups/snipeit.sql
docker volume ls --filter label=com.docker.compose.project=docker-admin-toolkit
```

Upgrade after reading upstream release notes:

```bash
docker compose pull && docker compose up -d --build
```

IT-Tools, CyberChef, Gatus, SO-CRATES, ConvertX, and MyIP track moving channels; pin tags in `.env` for reproducible deploys. Stirling-PDF is pinned by digest (see `SOURCES.md`).

## Notes

- Snipe-IT logs mail instead of sending it; configure SMTP before relying on email.
- Stirling-PDF may force a password change on first login; the `.env` password does not reset an existing account.
- Add monitors in `config/gatus/config.yaml`.

## Files

- `compose.yml` — all ten tools, their dependencies, and the dashboard; `compose.proxy.yml` — optional reverse-proxy overlay
- `.env.example` — defaults and secret placeholders
- `setup.sh`, `start.sh`, `stop.sh` (+ macOS `.command` wrappers)
- `dashboard/` — Python standard-library server and static UI, no external dependencies
- `config/` — Gatus monitors and NetBox configuration
- `proxy/Caddyfile.example` — sample Caddy routes
- `SOURCES.md` — upstream references and image notes

## License

MIT for the toolkit's own files (see `LICENSE`). Bundled applications are under their respective upstream licenses.
