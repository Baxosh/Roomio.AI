# Vanna AI Deployment Guide

This guide covers deploying the Vanna AI application in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Configuration](#configuration)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.12+
- **Existing PostgreSQL database** (GRMS) with access credentials
- Docker & Docker Compose (for containerized deployment)
- DeepSeek API key
- Network access to the PostgreSQL database

## Local Development

### 1. Clone and Setup

```bash
# Clone the repository
cd vanna_ai

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Install Dependencies

Using `uv` (recommended):

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync
```

Using `pip`:

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the application
python app.py
```

The application will be available at `http://localhost:8000`

## Docker Deployment

**Note**: This application connects to an **existing PostgreSQL database**. Ensure your database is running and accessible before starting the application.

### Using Docker Compose (Recommended)

#### 1. Configure Environment

Edit `.env` with your **existing database** credentials:

```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

**Important**: Set `POSTGRES_HOST` to your database server:
- If database is on the same host: `POSTGRES_HOST=host.docker.internal` (or the host IP)
- If database is on a remote server: `POSTGRES_HOST=your-db-server.com`
- If using localhost development: `POSTGRES_HOST=localhost` (and run without Docker)

#### 2. Start Application

```bash
# Build and start the application
docker-compose up -d

# View logs
docker-compose logs -f vanna-app

# Check status
docker-compose ps
```

#### 3. Stop Application

```bash
# Stop application
docker-compose down

# Note: This does NOT affect your external database
```

### Connecting to Local Database from Docker

If your PostgreSQL is running on the host machine (localhost), uncomment this in `docker-compose.yml`:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Then set in `.env`:
```bash
POSTGRES_HOST=host.docker.internal
```

### Using Docker Only

#### 1. Build Image

```bash
docker build -t vanna-ai:latest .
```

#### 2. Run Container

```bash
docker run -d \
  --name vanna-ai \
  -p 8000:8000 \
  -e DEEPSEEK_API_KEY=your-api-key \
  -e POSTGRES_HOST=your-db-host \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=grms \
  -e POSTGRES_USER=your-user \
  -e POSTGRES_PASSWORD=your-password \
  -e LOG_LEVEL=INFO \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/chroma_db:/app/chroma_db \
  -v $(pwd)/structure.txt:/app/structure.txt:ro \
  vanna-ai:latest
```

## Production Deployment

### Prerequisites

- Production-ready PostgreSQL database
- Reverse proxy (nginx/Caddy)
- SSL certificates
- Monitoring solution

### 1. External Database Requirements

Ensure your **existing** PostgreSQL database:
- Is accessible from the application server (firewall rules, network routing)
- Has proper credentials configured (read-only recommended for safety)
- Has SSL/TLS enabled (recommended for production)
- Has proper backups configured
- Optionally has connection pooling (e.g., PgBouncer) for better performance

### 2. Application Deployment

#### Option A: Docker Compose (Production)

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  vanna-app:
    image: vanna-ai:latest
    container_name: vanna-ai-prod
    restart: always
    ports:
      - "127.0.0.1:8000:8000"
    env_file:
      - .env.production
    volumes:
      - ./logs:/app/logs
      - ./chroma_db:/app/chroma_db
      - ./structure.txt:/app/structure.txt:ro
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

Deploy:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### Option B: Systemd Service

Create `/etc/systemd/system/vanna-ai.service`:

```ini
[Unit]
Description=Vanna AI Service
After=network.target postgresql.service

[Service]
Type=simple
User=vanna
Group=vanna
WorkingDirectory=/opt/vanna-ai
Environment="PATH=/opt/vanna-ai/.venv/bin"
EnvironmentFile=/opt/vanna-ai/.env
ExecStart=/opt/vanna-ai/.venv/bin/python /opt/vanna-ai/app.py
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/vanna-ai/logs /opt/vanna-ai/chroma_db

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable vanna-ai
sudo systemctl start vanna-ai
sudo systemctl status vanna-ai
```

### 3. Reverse Proxy Configuration

#### Nginx

```nginx
upstream vanna_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name vanna.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name vanna.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://vanna_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Logging
    access_log /var/log/nginx/vanna-access.log;
    error_log /var/log/nginx/vanna-error.log;
}
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek API key | - | Yes |
| `POSTGRES_HOST` | Database host | localhost | Yes |
| `POSTGRES_PORT` | Database port | 5432 | Yes |
| `POSTGRES_DB` | Database name | postgres | Yes |
| `POSTGRES_USER` | Database user | postgres | Yes |
| `POSTGRES_PASSWORD` | Database password | - | Yes |
| `LOG_LEVEL` | Logging level | INFO | No |
| `APP_PORT` | Application port | 8000 | No |
| `AGENT_MAX_ITERATIONS` | Max tool iterations | 50 | No |
| `LLM_TEMPERATURE` | LLM temperature | 0.7 | No |

### Database Schema

Ensure `structure.txt` contains your latest database schema. Update it using:

```bash
python extract_schema.py > structure.txt
```

## Monitoring and Logging

### Logs

Logs are written to:
- File: `logs/vanna_app.log` (configurable via `LOG_FILE`)
- Console: stdout/stderr

Log rotation is automatic (10MB per file, 5 backups).

### Log Levels

```bash
# Production
LOG_LEVEL=INFO

# Development
LOG_LEVEL=DEBUG

# Critical only
LOG_LEVEL=ERROR
```

### Viewing Logs

Local:
```bash
tail -f logs/vanna_app.log
```

Docker:
```bash
docker-compose logs -f vanna-app
```

Systemd:
```bash
journalctl -u vanna-ai -f
```

### Health Checks

The application includes a health check endpoint:

```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Application Won't Start

1. **Check configuration validation:**
   ```bash
   python -c "from config import config; print(config.validate())"
   ```

2. **Check logs:**
   ```bash
   tail -100 logs/vanna_app.log
   ```

3. **Verify environment variables:**
   ```bash
   python -c "from config import config; print(config)"
   ```

### Database Connection Issues

1. **Test database connectivity from application host:**
   ```bash
   psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB
   ```

2. **Check network connectivity:**
   ```bash
   # Test port accessibility
   telnet $POSTGRES_HOST $POSTGRES_PORT
   # Or use nc
   nc -zv $POSTGRES_HOST $POSTGRES_PORT
   ```

3. **Docker to host.docker.internal issues:**
   - Ensure `extra_hosts` is configured in docker-compose.yml
   - Or use the actual host IP instead of localhost
   - Check Docker network settings: `docker network inspect vanna-network`

4. **Verify credentials in `.env` file**

5. **Check PostgreSQL allows remote connections:**
   - Verify `pg_hba.conf` allows your application's IP
   - Verify `postgresql.conf` has `listen_addresses` set correctly

### Memory Issues

If the application uses too much memory:

1. Reduce `AGENT_MAX_ITERATIONS`
2. Set `LLM_MAX_TOKENS` to limit response size
3. Increase Docker memory limits

### API Rate Limiting

If you hit DeepSeek rate limits:

1. Reduce `LLM_TEMPERATURE` for more consistent responses
2. Implement request queuing
3. Upgrade DeepSeek API plan

### Permission Issues

Docker:
```bash
# Fix log directory permissions
sudo chown -R 1000:1000 logs chroma_db

# Or run as specific user
docker run --user $(id -u):$(id -g) ...
```

Systemd:
```bash
# Fix ownership
sudo chown -R vanna:vanna /opt/vanna-ai
```

## Backup and Recovery

### Backup ChromaDB

```bash
# Local
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Docker
docker-compose exec vanna-app tar -czf /tmp/chroma_backup.tar.gz /app/chroma_db
docker cp vanna-ai-app:/tmp/chroma_backup.tar.gz .
```

### Restore ChromaDB

```bash
# Local
tar -xzf chroma_backup_YYYYMMDD.tar.gz

# Docker
docker cp chroma_backup.tar.gz vanna-ai-app:/tmp/
docker-compose exec vanna-app tar -xzf /tmp/chroma_backup.tar.gz -C /
```

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong passwords** for database
3. **Rotate API keys** regularly
4. **Enable SSL/TLS** in production
5. **Keep dependencies updated**: `uv sync --upgrade`
6. **Use firewall rules** to restrict database access
7. **Enable audit logging** for sensitive operations
8. **Implement rate limiting** at reverse proxy level

## Support

For issues and questions:
- Check logs first: `logs/vanna_app.log`
- Review this documentation
- Check application configuration: `python -c "from config import config; print(config)"`
