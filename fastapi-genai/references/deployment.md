# Deployment

## Deployment Target — Pick by Workload Shape

| Option | Best for | Trade-off |
|---|---|---|
| **VM** | Direct control, GPU access, security-critical workloads | Highest maintenance burden, pay 24/7 |
| **Serverless** | Low/spiky volume, event-driven | Short timeouts (often ~10 min) — wrong fit for long generations |
| **Managed platform (PaaS)** | Fast iteration, delegated ops | Usually CPU-only, higher per-unit cost |
| **Containers** | Portability, reproducibility, scaling | Needs orchestration once beyond a single instance |

Default to containers unless there's a specific reason (a hard GPU requirement → VM;
genuinely spiky/low/event-driven traffic → serverless).

## Dockerfile — Core Pattern

```dockerfile
FROM python:3.12-slim AS base
WORKDIR /code

# Install deps BEFORE copying code — keeps the expensive layer cached
# across rebuilds that only change application code, not requirements.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Layer ordering is the single biggest build-time lever**: put stable, expensive steps
(installing dependencies) before volatile, cheap steps (copying your actual code), so a
code change doesn't invalidate the dependency-install cache layer.

## Run as a Non-Root User

```dockerfile
ARG USERNAME=fastapi
ARG USER_UID=1001
RUN groupadd --gid $USER_UID $USERNAME \
    && adduser --uid $USER_UID --gid $USER_UID --no-create-home --disabled-password $USERNAME
USER $USERNAME
```

Don't run a network-facing service as root in the container — this is a default, not an
edge case to consider only for "security-critical" services.

## Minimize Image Size

- Use `python:3.12-slim` (or `alpine` if size is critical) over a full base image.
- If shipping a self-hosted model with GPU inference libraries (PyTorch + Transformers can
  be several GB), consider ONNX runtime + quantization instead — this alone can take an
  image from multiple GB down to tens of MB for smaller models.
- Use `.dockerignore` to keep `.venv`, `.git`, `__pycache__`, and `.env` out of the build
  context.
- **Multi-stage builds** for the largest wins: a `base` stage that installs dependencies
  and downloads any model weights, a `production` stage that copies only what's needed to
  run, and optionally a `development` stage on top of `production` with dev tools added.
  This is the difference between a ~1.4GB image and a ~30-50MB one in practice.

```dockerfile
FROM python:3.12-slim AS base
RUN python -m venv /opt/venv
COPY requirements.txt .
RUN /opt/venv/bin/pip install -r requirements.txt

FROM base AS production
COPY --from=base /opt/venv /opt/venv
WORKDIR /code
COPY . .
CMD ["/opt/venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM production AS development
COPY requirements-dev.txt .
RUN /opt/venv/bin/pip install -r requirements-dev.txt
CMD ["/opt/venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

```bash
docker build --target production -t genai-service:prod .
docker build --target development -t genai-service:dev .
```

## Networking

Use a user-defined bridge network so containers can resolve each other by service name
(embedded DNS), rather than `--net=host` (no isolation) or hardcoded IPs:

```bash
docker network create genai-net
docker run --network genai-net genai-service
docker run --network genai-net postgres
```

Bind published ports to `127.0.0.1` specifically when a service should only be reachable
from the host, not the wider network: `docker run -p 127.0.0.1:8000:8000 ...`.

## Docker Compose for Local Multi-Container Dev

```yaml
services:
  server:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: ${DATABASE_URL}
    secrets: [openai_api_token]
    networks: [genai-net]
  db:
    image: postgres:16-alpine
    volumes: ["db-data:/var/lib/postgresql/data"]
    networks: [genai-net]

volumes:
  db-data:
networks:
  genai-net:
    driver: bridge
secrets:
  openai_api_token:
    environment: OPENAI_API_KEY
```

Use a `compose.override.yml` for local-dev-only settings (volume mounts for live reload,
dev credentials) layered on top of the base `compose.yml` used in every environment.

## GPU Support

```bash
docker run --gpus=all nvidia/cuda:12.0-runtime-ubuntu22.04 nvidia-smi
```

```yaml
services:
  app:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Only relevant for self-hosted model inference — calling a hosted provider API needs no GPU
access on your side at all.

## Health Checks and Startup Time

If the container loads a model (local weights) at startup, give the health check a
generous initial grace period — a slow model load that looks like a crashed container to
an orchestrator will get killed and restarted in a loop, never actually becoming healthy.
