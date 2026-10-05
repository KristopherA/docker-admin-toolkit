"""Minimal environment-driven NetBox configuration for this Compose bundle."""

import os


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() == "true"


ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost 127.0.0.1").split()
# Health checks use localhost; dashboard and Gatus use the Compose service name.
for monitoring_host in ("localhost", "netbox"):
    if monitoring_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(monitoring_host)

# HTTPS access through an optional reverse proxy (compose.proxy.yml).
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split()

DATABASES = {
    "default": {
        "NAME": os.getenv("DB_NAME", "netbox"),
        "USER": os.getenv("DB_USER", "netbox"),
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.getenv("DB_HOST", "netbox-postgres"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 300,
    }
}

REDIS = {
    "tasks": {
        "HOST": os.getenv("REDIS_HOST", "netbox-redis"),
        "PORT": int(os.getenv("REDIS_PORT", "6379")),
        "PASSWORD": os.environ["REDIS_PASSWORD"],
        "DATABASE": 0,
        "SSL": False,
    },
    "caching": {
        "HOST": os.getenv("REDIS_CACHE_HOST", "netbox-redis-cache"),
        "PORT": int(os.getenv("REDIS_CACHE_PORT", "6379")),
        "PASSWORD": os.environ["REDIS_CACHE_PASSWORD"],
        "DATABASE": 1,
        "SSL": False,
    },
}

SECRET_KEY = os.environ["SECRET_KEY"]
API_TOKEN_PEPPERS = {1: os.environ["API_TOKEN_PEPPER_1"]}

LOGIN_REQUIRED = True
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")
MEDIA_ROOT = "/opt/netbox/netbox/media"
METRICS_ENABLED = env_bool("METRICS_ENABLED", False)
CENSUS_REPORTING_ENABLED = env_bool("CENSUS_REPORTING_ENABLED", False)
COPILOT_ENABLED = env_bool("COPILOT_ENABLED", False)
RELEASE_CHECK_URL = None
