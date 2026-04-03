"""Tests for FM-080 — Production deployment foundation.

Validates that production deployment files exist and are well-formed.
"""

import pathlib

import yaml

# Workspace root: tests/ -> api/ -> apps/ -> Forgemind/
_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _load_yaml(path: pathlib.Path) -> dict:
    """Load a YAML/Docker Compose file."""
    return yaml.safe_load(path.read_text())


# ── Production Compose ───────────────────────────────────────


def test_prod_compose_exists():
    """docker-compose.prod.yml exists."""
    assert (_ROOT / "docker-compose.prod.yml").exists()


def test_prod_compose_services():
    """Production compose defines expected services."""
    compose = _load_yaml(_ROOT / "docker-compose.prod.yml")
    services = set(compose.get("services", {}).keys())
    assert {"postgres", "redis", "api", "web", "worker", "nginx"} <= services


def test_prod_compose_no_volume_mounts():
    """Production compose does not bind-mount source code (no hot-reload)."""
    compose = _load_yaml(_ROOT / "docker-compose.prod.yml")
    for name, svc in compose["services"].items():
        volumes = svc.get("volumes", [])
        for v in volumes:
            if isinstance(v, str) and v.startswith("./apps/"):
                raise AssertionError(f"Service '{name}' bind-mounts source code: {v}")


def test_prod_compose_required_env_vars():
    """Production compose enforces critical env vars with :? syntax."""
    content = (_ROOT / "docker-compose.prod.yml").read_text()
    assert "SECRET_KEY:?" in content or "SECRET_KEY:?SECRET_KEY" in content, (
        "SECRET_KEY should be required"
    )
    assert "POSTGRES_PASSWORD:?" in content, "POSTGRES_PASSWORD should be required"


# ── Production Dockerfiles ───────────────────────────────────


def test_api_dockerfile_prod_exists():
    """apps/api/Dockerfile.prod exists."""
    assert (_ROOT / "apps" / "api" / "Dockerfile.prod").exists()


def test_web_dockerfile_prod_exists():
    """apps/web/Dockerfile.prod exists."""
    assert (_ROOT / "apps" / "web" / "Dockerfile.prod").exists()


def test_api_dockerfile_prod_nonroot():
    """API production Dockerfile runs as non-root user."""
    content = (_ROOT / "apps" / "api" / "Dockerfile.prod").read_text()
    assert "USER" in content, "Should switch to non-root user"
    assert "appuser" in content


def test_web_dockerfile_prod_nonroot():
    """Web production Dockerfile runs as non-root user."""
    content = (_ROOT / "apps" / "web" / "Dockerfile.prod").read_text()
    assert "USER" in content, "Should switch to non-root user"
    assert "appuser" in content


def test_api_dockerfile_prod_healthcheck():
    """API production Dockerfile includes HEALTHCHECK."""
    content = (_ROOT / "apps" / "api" / "Dockerfile.prod").read_text()
    assert "HEALTHCHECK" in content


# ── Nginx config ─────────────────────────────────────────────


def test_nginx_config_exists():
    """deploy/nginx.conf exists."""
    assert (_ROOT / "deploy" / "nginx.conf").exists()


def test_nginx_config_security_headers():
    """Nginx config includes security headers."""
    content = (_ROOT / "deploy" / "nginx.conf").read_text()
    assert "X-Frame-Options" in content
    assert "X-Content-Type-Options" in content
    assert "Strict-Transport-Security" in content


def test_nginx_config_routes():
    """Nginx config proxies to api and web services."""
    content = (_ROOT / "deploy" / "nginx.conf").read_text()
    assert "upstream api" in content
    assert "upstream web" in content
    assert "proxy_pass http://api" in content
    assert "proxy_pass http://web" in content


# ── Deployment docs ──────────────────────────────────────────


def test_deployment_readme_exists():
    """docs/DEPLOYMENT.md exists."""
    assert (_ROOT / "docs" / "DEPLOYMENT.md").exists()


def test_deployment_readme_covers_essentials():
    """Deployment README covers environment, health, security, and TLS."""
    content = (_ROOT / "docs" / "DEPLOYMENT.md").read_text()
    assert "SECRET_KEY" in content
    assert "/health" in content
    assert "TLS" in content or "HTTPS" in content
    assert "Security" in content


def test_env_production_exists():
    """Production env example file exists."""
    assert (_ROOT / ".env.production").exists()


def test_env_production_marks_required():
    """Production env file documents required variables."""
    content = (_ROOT / ".env.production").read_text()
    assert "REQUIRED" in content
    assert "SECRET_KEY=" in content
    assert "POSTGRES_PASSWORD=" in content
