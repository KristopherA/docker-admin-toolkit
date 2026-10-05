"""Local launcher and bounded availability probes; no Docker socket or secrets."""
import concurrent.futures
import json
import os
from pathlib import Path
import threading
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOT = Path(__file__).parent / "static"
SERVICES = [
    ("it-tools", "IT-Tools", "Utilities", "Encode, calculate, and convert everyday data.", "IT_TOOLS_PORT", 8081, "http://it-tools:80/", "tools", "it-tools"),
    ("cyberchef", "CyberChef", "Utilities", "Build recipes to decode and transform data.", "CYBERCHEF_PORT", 8082, "http://cyberchef:8080/", "recipe", "cyberchef"),
    ("stirling-pdf", "Stirling-PDF", "Documents", "Merge, split, compress, and OCR your PDFs.", "STIRLING_PDF_PORT", 8083, "http://stirling-pdf:8080/", "pdf", "pdf"),
    ("uptime-kuma", "Uptime Kuma", "Monitoring", "Keep an eye on websites and service uptime.", "UPTIME_KUMA_PORT", 3001, "http://uptime-kuma:3001/", "pulse", "uptime"),
    ("gatus", "Gatus", "Monitoring", "View automated checks across the toolkit.", "GATUS_PORT", 8084, "http://gatus:8080/", "checks", "gatus"),
    ("netbox", "NetBox", "Inventory", "Document devices, networks, and IP addresses.", "NETBOX_PORT", 8000, "http://netbox:8080/login/", "network", "netbox"),
    ("snipe-it", "Snipe-IT", "Inventory", "Track equipment, ownership, and check-outs.", "SNIPEIT_PORT", 8001, "http://snipe-it:80/", "asset", "snipeit"),
    ("convertx", "ConvertX", "Documents", "Convert images, audio, video, ebooks, and more between formats.", "CONVERTX_PORT", 8087, "http://convertx:3000/", "convert", "convertx"),
    ("myip", "MyIP", "Utilities", "Check public IP, DNS and WebRTC leaks, connectivity, and whois.", "MYIP_PORT", 8088, "http://myip:18966/", "globe", "myip"),
    ("so-crates", "SO-CRATES", "Security", "Analyze PCAPs, binaries, and logs with Suricata, YARA, and Sigma.", "SOCRATES_PORT", 8085, "http://so-crates:8000/", "shield", "socrates"),
]

# External web services: link-only cards. Never probed (bot protection returns false
# errors, and probing would contact third parties every 15 s). Public sandboxes can
# publish submissions: only upload samples you are authorized to share.
LINKS = [
    ("any-run", "ANY.RUN", "Sandboxes", "Interactive sandbox: click through and watch a sample detonate live.", "https://app.any.run/", "sandbox"),
    ("hybrid-analysis", "Hybrid Analysis", "Sandboxes", "CrowdStrike Falcon reports and search across 1.5B+ IOCs.", "https://hybrid-analysis.com/", "sandbox"),
    ("triage", "Recorded Future Triage", "Sandboxes", "Fast automated verdicts with config extraction for many families.", "https://tria.ge/", "sandbox"),
    ("joe-sandbox", "Joe Sandbox", "Sandboxes", "Deep reports with behavior graphs and screenshots, Windows through iOS.", "https://www.joesandbox.com/", "sandbox"),
    ("cape-public", "CAPE Sandbox", "Sandboxes", "Open-source Cuckoo successor; unpacks payloads and extracts configs.", "https://capesandbox.com/", "sandbox"),
    ("intezer", "Intezer Analyze", "Sandboxes", "Genetic analysis: shows which malware family the code was reused from.", "https://analyze.intezer.com/", "sandbox"),
    ("filescan", "Filescan.io", "Sandboxes", "Emulation-based triage that returns IOCs in seconds.", "https://www.filescan.io/", "sandbox"),
    ("urlscan", "urlscan.io", "URL Check", "Detonate a URL in a browser sandbox and inspect what it loads.", "https://urlscan.io/", "globe"),
    ("virustotal", "VirusTotal", "URL Check", "Scan files, URLs, domains, and IPs against 70+ engines.", "https://www.virustotal.com/", "globe"),
    ("urlhaus", "URLhaus", "URL Check", "abuse.ch database of known malware distribution URLs.", "https://urlhaus.abuse.ch/", "globe"),
    ("checkphish", "CheckPhish", "URL Check", "AI phishing detection for suspicious links.", "https://checkphish.bolster.ai/", "globe"),
    ("sucuri", "Sucuri SiteCheck", "URL Check", "Scan a whole website for malware and blocklisting.", "https://sitecheck.sucuri.net/", "globe"),
    ("talos", "Cisco Talos", "URL Check", "Domain, IP, and email sender reputation lookups.", "https://talosintelligence.com/", "globe"),
]

DOMAIN = os.getenv("TOOLKIT_DOMAIN", "").strip()
LINK_HOST = os.getenv("LINK_HOST", "localhost").strip() or "localhost"

def service_url(s):
    # HTTPS via the reverse proxy when a domain is set; otherwise LINK_HOST:port.
    return f"https://{s[8]}.{DOMAIN}/" if DOMAIN else f"http://{LINK_HOST}:{int(os.getenv(s[4], s[5]))}/"

def service_catalog():
    return [dict(id=s[0], name=s[1], category=s[2], description=s[3],
                 port=int(os.getenv(s[4], s[5])), url=service_url(s), icon=s[7]) for s in SERVICES] + \
           [dict(id=l[0], name=l[1], category=l[2], description=l[3], port=None,
                 url=l[4], icon=l[5], external=True) for l in LINKS]

# Don't follow an application's redirects to an arbitrary external host.
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

OPENER = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))
def probe(service):
    started = time.monotonic()
    try:
        request = urllib.request.Request(service[6], headers={"User-Agent": "Toolkit-Dashboard/1.0"})
        try:
            with OPENER.open(request, timeout=4) as response:
                code = response.status
        except urllib.error.HTTPError as error:
            code = error.code
            error.close()
        state = "ready" if 200 <= code < 400 or code in (401, 403) else "attention"
        return service[0], {"state": state, "httpCode": code,
                            "latencyMs": round((time.monotonic() - started) * 1000)}
    except (OSError, urllib.error.URLError, ValueError):
        return service[0], {"state": "unavailable", "httpCode": None, "latencyMs": None}

CACHE = {"checkedAt": None, "services": {}}
CACHE_LOCK = threading.Lock()

def check_services():
    while True:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(SERVICES)) as pool:
            states = dict(pool.map(probe, SERVICES))
        with CACHE_LOCK:
            CACHE.update(checkedAt=int(time.time()), services=states)
        time.sleep(15)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        super().end_headers()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/health":
            data = {"ok": True}
        elif path == "/api/services":
            data = service_catalog()
        elif path == "/api/status":
            with CACHE_LOCK:
                data = {"checkedAt": CACHE["checkedAt"], "services": dict(CACHE["services"])}
        elif path in ("/", "/index.html", "/style.css", "/app.js", "/favicon.svg"):
            return super().do_GET()
        else:
            return self.send_error(404)
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    threading.Thread(target=check_services, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
