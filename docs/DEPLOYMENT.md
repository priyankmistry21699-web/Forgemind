# ForgeMind — Production Deployment Guide

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- A domain name with DNS pointing to your server
- TLS certificates (Let's Encrypt recommended)
- At least 2 GB RAM, 2 CPU cores

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/priyankmistry21699-web/Forgemind.git
cd Forgemind

# 2. Create and configure environment
cp .env.production .env
# Edit .env with your production values (see below)

# 3. Place TLS certificates
cp /path/to/fullchain.pem deploy/certs/fullchain.pem
cp /path/to/privkey.pem deploy/certs/privkey.pem

# 4. Build and start
docker compose -f docker-compose.prod.yml up -d --build

# 5. Verify health
curl http://localhost/health
curl http://localhost/health/ready
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing secret (min 32 chars) | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | Database password | Strong random password |
| `CORS_ORIGINS` | Allowed CORS origins | `https://forgemind.example.com` |
| `NEXT_PUBLIC_API_URL` | Public API URL for frontend | `https://forgemind.example.com` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `forgemind` | Database name |
| `POSTGRES_USER` | `forgemind` | Database user |
| `REDIS_PASSWORD` | *(empty)* | Redis auth password |
| `API_WORKERS` | `2` | Uvicorn worker count |
| `WORKER_POLL_INTERVAL` | `5` | Background worker poll interval (seconds) |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key for LLM planner |
| `ANTHROPIC_API_KEY` | *(empty)* | Anthropic API key (alternative) |
| `GOOGLE_API_KEY` | *(empty)* | Google AI API key (alternative) |
| `HTTP_PORT` | `80` | Nginx HTTP port |
| `HTTPS_PORT` | `443` | Nginx HTTPS port |

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Nginx (reverse proxy, TLS termination)         │
│  :80 → redirect to :443                         │
│  :443 → routes to api / web                     │
├─────────────────────┬───────────────────────────┤
│  Web (Next.js)      │  API (FastAPI/Uvicorn)    │
│  :3000 (internal)   │  :8000 (internal)         │
├─────────────────────┴───────────────────────────┤
│  Worker (background task processor)              │
├─────────────────────┬───────────────────────────┤
│  PostgreSQL 16      │  Redis 7                  │
│  :5432 (internal)   │  :6379 (internal)         │
└─────────────────────┴───────────────────────────┘
```

All services communicate over an internal Docker network. Only Nginx
exposes ports to the host.

## Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness check — API process is running |
| `GET /health/ready` | Readiness check — API + database connection verified |
| `GET /metrics` | Prometheus-compatible metrics (counters, histograms) |

## Security Checklist

- [ ] `SECRET_KEY` is a unique random value (not the default `change-me-to-a-random-secret`)
- [ ] `POSTGRES_PASSWORD` is a strong random password
- [ ] `DEBUG` is set to `false`
- [ ] TLS certificates are in place (`deploy/certs/`)
- [ ] `CORS_ORIGINS` is restricted to your actual domain
- [ ] `/metrics` endpoint access is restricted (see nginx.conf comments)
- [ ] Database is not exposed to the public network
- [ ] LLM API keys are set if using planner features

## TLS with Let's Encrypt

```bash
# Install certbot
apt install certbot

# Generate certificate (stop nginx first, or use webroot)
certbot certonly --standalone -d forgemind.example.com

# Copy certs
cp /etc/letsencrypt/live/forgemind.example.com/fullchain.pem deploy/certs/
cp /etc/letsencrypt/live/forgemind.example.com/privkey.pem deploy/certs/

# Restart nginx
docker compose -f docker-compose.prod.yml restart nginx
```

Set up auto-renewal:
```bash
echo "0 3 * * * certbot renew --quiet && docker compose -f /path/to/docker-compose.prod.yml restart nginx" | crontab -
```

## Running Without TLS (Development/Staging)

Edit `deploy/nginx.conf`:
1. Remove or comment out the HTTPS server block
2. Change the HTTP server to proxy directly instead of redirecting:

```nginx
server {
    listen 80;
    server_name _;
    # ... add proxy_pass directives from the HTTPS block ...
}
```

## Monitoring

The `/metrics` endpoint exposes Prometheus-compatible metrics:

```bash
# Check metrics
curl -s https://forgemind.example.com/metrics

# Key metrics:
# http_requests_total{method, path, status}  — request counter
# http_request_duration_seconds               — latency histogram
# http_errors_total                           — 5xx error counter
```

To integrate with Prometheus, add to your `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: "forgemind"
    static_configs:
      - targets: ["forgemind-api:8000"]
```

## Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f api

# API access logs include request IDs and timing:
# [a1b2c3d4] GET /api/v1/projects → 200 (12.3ms)
```

## Backup

```bash
# Database backup
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U forgemind forgemind > backup_$(date +%Y%m%d).sql

# Restore
docker compose -f docker-compose.prod.yml exec -i postgres \
  psql -U forgemind forgemind < backup_20240101.sql
```

## Updating

```bash
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```
