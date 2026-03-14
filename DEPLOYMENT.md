# Deployment Guide

## Docker Compose

```bash
# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your OpenAI API key

# Build and start
docker compose up --build
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## Kubernetes

See deployment manifests in `k8s/` (to be added)

## Cloud Platforms

### AWS, GCP, Heroku

Setup instructions coming soon.
