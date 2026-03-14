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

## Azure Static Web Apps (GitHub Actions)

Pushes to `main` (and PRs targeting `main`) automatically build and deploy the **frontend** to Azure Static Web Apps.

### Setup

1. **Create an Azure Static Web App** (Azure portal or CLI) and link it to this repo if desired, or use the existing one.
2. **Add GitHub secret** (repo → Settings → Secrets and variables → Actions):
   - `AZURE_STATIC_WEB_APPS_API_TOKEN_PURPLE_WAVE_075D2CA10` = deployment token from Azure (Static Web App → Manage deployment token).
3. **Optional – production backend URL**: add a repo **Variable** (Settings → Secrets and variables → Actions → Variables):
   - `REACT_APP_API_BASE_URL` = your deployed backend URL (e.g. `https://your-backend.azurewebsites.net`).  
   If unset, the frontend uses `http://localhost:8000` (fine for local dev; set this for production).

### Workflow

- **File:** `.github/workflows/azure-static-web-apps.yml`
- **Triggers:** `push` to `main`, `pull_request` (opened/synchronized/reopened/closed) for `main`
- **Build:** Frontend is built from `/frontend` with output `build`; no API is deployed by this workflow (backend must be hosted separately, e.g. Azure Container Apps or App Service).

## Cloud Platforms

### AWS, GCP, Heroku

Setup instructions coming soon.
