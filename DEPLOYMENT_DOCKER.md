# Docker Deployment Guide

## Overview

This guide explains how to build and deploy the Regulation Navigator MVP using Docker for containerized deployment.

## Quick Start

### Prerequisites
- Docker Desktop installed
- Docker Compose installed (usually comes with Docker Desktop)
- Azure OpenAI credentials (if using LLM features)

### 1. Build Docker Image

```bash
# Navigate to project root
cd /workspaces/reg-nav-mvp

# Build image
docker build -t regulation-navigator:latest .

# Verify build
docker images | grep regulation-navigator
```

### 2. Run Container Locally

#### Option A: Basic Run
```bash
# Run with environment variables
docker run -p 8000:8000 \
  -e AZURE_OPENAI_KEY="your-key" \
  -e AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/" \
  -e AZURE_OPENAI_DEPLOYMENT="gpt-4-turbo-preview" \
  regulation-navigator:latest
```

#### Option B: Using docker-compose (Recommended)
```bash
# Create .env file with credentials
cat > .env <<EOF
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo-preview
EOF

# Start services
docker-compose up

# View logs
docker-compose logs -f regulation-navigator

# Stop services
docker-compose down
```

### 3. Test the API

```bash
# Health check
curl -X GET http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is customer due diligence?",
    "top_k": 3
  }'
```

## Image Details

### Multi-Stage Build

The Dockerfile uses a 2-stage build for efficiency:

**Stage 1: Builder**
- Uses `python:3.12-slim` base
- Installs build dependencies
- Creates virtual environment
- Installs Python packages

**Stage 2: Runtime**
- Uses clean `python:3.12-slim` base
- Copies virtual environment from builder
- Copies application files
- Creates non-root user (security)
- Runs Uvicorn server

### Benefits
- Smaller final image size (~500MB vs 1GB+)
- Faster build times (dependencies cached)
- Security: runs as non-root user
- Health checks built-in
- Automatic restart on failure

## Image Specifications

| Property | Value |
|----------|-------|
| Base Image | `python:3.12-slim` |
| Working Directory | `/app` |
| User | `appuser` (UID 1000) |
| Port | `8000` |
| Health Check | Every 30s, 10s timeout, 5s startup period |

## Environment Variables

Required for LLM functionality:

```bash
AZURE_OPENAI_KEY=<azure-openai-api-key>
AZURE_OPENAI_ENDPOINT=<azure-openai-endpoint-url>
AZURE_OPENAI_DEPLOYMENT=<deployment-name>
```

Optional:

```bash
LOG_LEVEL=info|debug|warning|error
REGULATIONS_FILE=data.txt  # Path to data source
PYTHONUNBUFFERED=1        # Real-time log output
```

## Docker Compose Services

### regulation-navigator (Main Service)
- FastAPI application
- Port: 8000
- Health checks enabled
- Auto-restart on failure
- Volume mounts for data file

### nginx (Optional Reverse Proxy)
```bash
# Enable with profile
docker-compose --profile with-proxy up
```

## Building Variants

### Development Build
```bash
# Includes test dependencies
docker build --target builder -t regulation-navigator:dev .
```

### Production Build
```bash
# Optimized for performance
docker build --build-arg PYTHON_VERSION=3.12 \
  -t regulation-navigator:prod .
```

### Minimal Image
```bash
# Strip docs and examples
docker build --build-arg INSTALL_DOCS=false \
  -t regulation-navigator:minimal .
```

## Publishing to Registry

### Azure Container Registry (ACR)
```bash
# Login
az acr login --name myregistry

# Tag image
docker tag regulation-navigator:latest \
  myregistry.azurecr.io/regulation-navigator:latest

# Push
docker push myregistry.azurecr.io/regulation-navigator:latest

# View image
az acr repository show-tags --name myregistry \
  --repository regulation-navigator
```

### Docker Hub
```bash
# Login
docker login

# Tag image
docker tag regulation-navigator:latest \
  username/regulation-navigator:latest

# Push
docker push username/regulation-navigator:latest
```

### GitHub Container Registry (GHCR)
```bash
# Login
echo $TOKEN | docker login ghcr.io -u username --password-stdin

# Tag image
docker tag regulation-navigator:latest \
  ghcr.io/username/regulation-navigator:latest

# Push
docker push ghcr.io/username/regulation-navigator:latest
```

## Running Multiple Instances

### With Docker Compose Scaling
```bash
# Scale to 3 instances (with load balancer)
docker-compose up --scale regulation-navigator=3
```

### With Load Balancer (Nginx)
```bash
docker-compose --profile with-proxy up
```

Config in `nginx.conf`:
```nginx
upstream api {
    server regulation-navigator:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://api;
    }
}
```

## Monitoring & Logging

### View Logs
```bash
# Real-time logs
docker-compose logs -f regulation-navigator

# Last 100 lines
docker logs --tail 100 regulation-navigator

# Only errors
docker logs regulation-navigator | grep ERROR
```

### Health Status
```bash
# Check health
docker-compose ps

# Manual health check
curl http://localhost:8000/health
```

### Performance Monitoring
```bash
# View resource usage
docker stats regulation-navigator

# Memory limit exceeded? Scale up
docker run -m 2g -p 8000:8000 regulation-navigator:latest
```

## Volume Management

### Data Persistence
```bash
# Mount data.txt as read-only
docker run -v $(pwd)/data.txt:/app/data.txt:ro \
  -p 8000:8000 regulation-navigator:latest
```

### Logs Volume
```bash
# Mount logs directory
docker run -v $(pwd)/logs:/app/logs \
  -p 8000:8000 regulation-navigator:latest
```

## Networking

### Bridge Network (Default)
```bash
docker run --network bridge -p 8000:8000 regulation-navigator:latest
```

### Custom Network
```bash
# Create network
docker network create regnav-net

# Run services on network
docker run --network regnav-net --name api regulation-navigator:latest
docker run --network regnav-net --name proxy myimage:latest
```

## Security Best Practices

### 1. Non-Root User
- Container runs as `appuser` (UID 1000)
- No shell access by default
- Read-only filesystems where possible

### 2. Secret Management
```bash
# Use Docker secrets (Swarm mode)
echo "secret-value" | docker secret create app_secret -

# Or use environment files
docker run --env-file=.env.prod regulation-navigator:latest
```

### 3. Image Scanning
```bash
# Scan for vulnerabilities
docker scan regulation-navigator:latest

# Use Snyk
snyk container test regulation-navigator:latest
```

### 4. Registry Security
```bash
# Enable image signing
docker content trust enable

# Sign image
docker trust sign regulation-navigator:latest
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs regulation-navigator

# Inspect image
docker inspect regulation-navigator:latest

# Run with interactive shell
docker run -it regulation-navigator:latest /bin/bash
```

### Out of Memory
```bash
# Increase memory limit
docker run -m 2g regulation-navigator:latest

# Check current usage
docker stats regulation-navigator
```

### Port Already in Use
```bash
# Use different port
docker run -p 8001:8000 regulation-navigator:latest

# Find process using port 8000
lsof -i :8000
```

### API Timeouts
```bash
# Increase request timeout
docker run -e TIMEOUT=60 regulation-navigator:latest

# Check LLM latency
curl -w "@curl-format.txt" http://localhost:8000/ask
```

## Performance Tuning

### Uvicorn Workers
```bash
# Increase workers for better concurrency
docker run -e WORKERS=4 regulation-navigator:latest
```

### Python Optimization
```bash
# Enable bytecode optimization
docker run -e PYTHONOPTIMIZE=2 regulation-navigator:latest
```

### JIT Compilation
```bash
# Use PyPy for faster execution (if compatible)
FROM pypy:3.12-slim-buster
```

## Cleanup

```bash
# Stop and remove container
docker-compose down

# Remove images
docker rmi regulation-navigator:latest

# Remove volumes
docker volume prune

# Remove all unused resources
docker system prune -a
```

## CI/CD Integration

### GitHub Actions
```yaml
name: Docker Build and Push

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: docker/build-push-action@v2
        with:
          push: true
          tags: ghcr.io/user/regulation-navigator:latest
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
```

### DockerHub Automation
- Enable automated builds on push
- Configure build rules for branches/tags
- Automatic scanning on build

## Deployment Checklist

- [ ] Docker image builds successfully
- [ ] Container runs without errors
- [ ] Health check passes
- [ ] API responds to requests
- [ ] LLM integration works (with valid credentials)
- [ ] Data.txt correctly mounted
- [ ] Environment variables configured
- [ ] Logs are readable and informative
- [ ] Resource limits are appropriate
- [ ] Security best practices followed
