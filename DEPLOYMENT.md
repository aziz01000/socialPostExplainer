# Deployment Guide

## Production Deployment Checklist

### Pre-Deployment

- [ ] All environment variables configured
- [ ] OpenAI API key set and tested
- [ ] Database/vector store initialized
- [ ] Tests passing (run `make evaluate`)
- [ ] Security review completed
- [ ] Documentation updated

## Environment Configuration

### Backend (.env)

```bash
# Required
OPENAI_API_KEY=sk-...

# Recommended Production Settings
DEBUG=false
API_TITLE="Contextual Post Explainer"
LLM_PROVIDER=openai

# Guardrails (strongly recommended for production)
ENABLE_INPUT_MODERATION=true
ENABLE_OUTPUT_MODERATION=true

# Observability
PHOENIX_ENABLED=true
PHOENIX_PROJECT_NAME=contextual-post-explainer
PHOENIX_ENDPOINT=http://phoenix:6006

# Vector Store
TOP_K_DOCUMENTS=5
RERANK_TOP_K=3
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

Most suitable for production deployments.

#### 1. Prepare Environment

```bash
# Configure environment
cp backend/.env.example backend/.env
# Edit and set all required variables
nano backend/.env
```

#### 2. Build Images

```bash
# Build all services
docker-compose build

# Or build specific service
docker-compose build backend
docker-compose build frontend
```

#### 3. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

#### 4. Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000
```

### Option 2: Kubernetes

For large-scale deployments.

#### Create Kubernetes Manifests

```bash
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: post-explainer-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: post-explainer-backend
  template:
    metadata:
      labels:
        app: post-explainer-backend
    spec:
      containers:
      - name: backend
        image: post-explainer:backend-latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
        - name: DEBUG
          value: "false"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: post-explainer-backend-service
spec:
  selector:
    app: post-explainer-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace post-explainer

# Create secrets
kubectl create secret generic api-keys \
  --from-literal=openai=$OPENAI_API_KEY \
  -n post-explainer

# Deploy
kubectl apply -f backend-deployment.yaml -n post-explainer
kubectl apply -f frontend-deployment.yaml -n post-explainer

# Check deployment
kubectl get pods -n post-explainer
kubectl get svc -n post-explainer
kubectl logs deployment/post-explainer-backend -n post-explainer
```

### Option 3: Cloud Platforms

#### AWS (ECS + ECR)

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URL

docker tag post-explainer:backend $ECR_URL/post-explainer:backend
docker push $ECR_URL/post-explainer:backend

# Deploy via CloudFormation or ECS console
```

#### Google Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/$PROJECT_ID/post-explainer

# Deploy
gcloud run deploy post-explainer \
  --image gcr.io/$PROJECT_ID/post-explainer \
  --platform managed \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY
```

#### Heroku

```bash
# Login and create app
heroku login
heroku create post-explainer

# Configure environment
heroku config:set OPENAI_API_KEY=$OPENAI_API_KEY -a post-explainer

# Deploy via Git
git push heroku main

# View logs
heroku logs --tail -a post-explainer
```

## Scaling Considerations

### Horizontal Scaling

The backend is stateless and can be scaled horizontally:

```yaml
# docker-compose.yml with scaling
services:
  backend:
    build: ./backend
    ports:
      - "8000-8010:8000"  # Maps to multiple instances
    deployment:
      replicas: 5
```

### Caching Layer

Add Redis for embedding cache:

```python
# backend/app/cache.py
import redis

cache = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

async def get_cached_embeddings(text: str):
    cache_key = f"embedding:{hash(text)}"
    if cache.exists(cache_key):
        return json.loads(cache.get(cache_key))
    return None
```

### Load Balancing

Configure with Nginx or HAProxy:

```nginx
upstream backend {
    server backend1:8000 weight=5;
    server backend2:8000 weight=5;
    server backend3:8000 weight=5;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring & Observability

### Phoenix Dashboard

Access Phoenix tracing at `http://localhost:6006`

### Metrics Collection

Export traces and metrics:

```python
# backend/app/main.py
from app.observability import tracer

@app.on_event("shutdown")
async def export_metrics():
    tracer.export_traces("./metrics/traces.json")
```

### Logging

Configure centralized logging:

```bash
# docker-compose.yml
services:
  backend:
    logging:
      driver: "awslogs"  # or any other driver
      options:
        awslogs-group: "/ecs/post-explainer"
        awslogs-region: "us-east-1"
        awslogs-stream-prefix: "ecs"
```

## Security Hardening

### API Security

1. **Rate Limiting**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/explain")
@limiter.limit("100/minute")
async def explain_post(request: ExplainRequest):
    pass
```

2. **CORS Configuration**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict origins
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

3. **API Authentication**
```python
from fastapi import Depends, Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/explain")
async def explain_post(
    request: ExplainRequest,
    credentials: HTTPAuthCredentials = Depends(security)
):
    # Validate token
    pass
```

### Environment Variables

Never commit secrets:

```bash
# .env should be in .gitignore
# Use secret management services:
# - AWS Secrets Manager
# - Google Secret Manager
# - HashiCorp Vault
# - 1Password / LastPass
```

## Backup & Recovery

### Data Backups

```bash
# Backup FAISS index
cp -r backend/data /backup/faiss-$(date +%Y%m%d)

# Backup traces
cp backend/traces.json /backup/traces-$(date +%Y%m%d).json
```

### Database Snapshots

For production with persistent storage:

```yaml
volumes:
  vector-store:
    driver: local
  traces-storage:
    driver: local

# Regular backup cron job
0 2 * * * /scripts/backup-volumes.sh
```

## Performance Tuning

### Backend Optimization

1. **Connection Pooling**
```python
from httpx import AsyncClient

client = AsyncClient(
    limits=httpx.Limits(
        max_keepalive_connections=5,
        max_connections=20
    )
)
```

2. **Uvicorn Workers**
```bash
uvicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --max-requests 1000
```

3. **FAISS Optimization**
```python
# Use GPU FAISS if available
pip install faiss-gpu

# Configure batch processing
index = faiss.index_factory(dim, "HNSW32")
```

### Frontend Optimization

1. **Code Splitting**
```javascript
// React.lazy for route-based splitting
const ExplanationView = React.lazy(() => import('./components/ExplanationView'));
```

2. **Caching Headers**
```nginx
location ~* \.(js|css)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

## Disaster Recovery

### Failover Strategy

```yaml
# docker-compose with health checks and auto-restart
services:
  backend:
    restart: on-failure
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Rollback Procedure

```bash
# View deployment history
docker images

# Rollback to previous version
docker pull post-explainer:backend-v1.0.0
docker-compose up -d backend  # Will use latest tag by default
```

## Cost Optimization

### OpenAI API Costs

- **gpt-4o-mini**: ~$0.00015 per 1K input tokens, $0.0006 per 1K output tokens
- **embeddings (text-embedding-3-small)**: ~$0.02 per 1M tokens

**Strategies:**
- Cache embeddings (Redis)
- Batch inference requests
- Use cheaper models for non-critical tasks
- Monitor token usage with Phoenix

### Infrastructure Costs

- **Docker**: Free
- **Kubernetes**: ~$0.10/hour per node (AWS EKS)
- **Cloud Run**: $0.0000002 per GB-second (Google)
- **Storage**: ~$0.023 per GB/month (AWS S3)

## Next Steps

1. ✅ Set up monitoring dashboard
2. ✅ Configure automated backups
3. ✅ Set up CI/CD pipeline
4. ✅ Schedule regular security audits
5. ✅ Plan capacity based on usage
6. ✅ Document runbooks for on-call team
