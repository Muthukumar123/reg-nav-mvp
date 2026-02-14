# Deployment Guide

## Production Deployment Checklist

### Security
- Set strong API keys and rotate regularly
- Implement authentication and authorization
- Enable HTTPS/TLS encryption
- Configure CORS appropriately
- Set up rate limiting

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
EXPOSE 8000
CMD ["python", "-m", "src.api.main"]
```

Build and run:
```bash
docker build -t reg-nav-mvp .
docker run -d -p 8000:8000 -e OPENAI_API_KEY=your-key reg-nav-mvp
```

## Cloud Deployment

### AWS ECS
Push to ECR and deploy using ECS with appropriate task definitions.

### Azure Container Instances
Deploy using Azure Container Instances with environment variables.

### Google Cloud Run
Deploy as a Cloud Run service with appropriate memory and CPU settings.
