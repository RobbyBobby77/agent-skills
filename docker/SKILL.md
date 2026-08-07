---
name: docker
description: >
  Write and fix Dockerfiles, Compose files, multi-stage builds, image sizing,
  networking, volumes, and local dev containers. Use when containerizing apps,
  debugging container issues, optimizing images, or authoring docker-compose
  stacks. Do not use for Kubernetes-only cluster ops unless Docker is the focus.
---

# Docker

## Workflow

1. Inspect manifests, lockfiles, runtime commands, ports, health endpoints, and repository instructions.
2. Match the project's existing package manager and supported runtime; do not guess a newer version.
3. Build with the smallest necessary context and keep secrets out of layers and build arguments.
4. Run the image as its final non-root user and exercise the healthcheck or primary command.
5. Validate Compose configuration and report image size, exposed ports, and remaining assumptions.

## Dockerfile principles

1. **Multi-stage** — build tools in builder; tiny runtime image
2. **Layer caching** — copy dependency manifests before source
3. **Non-root user** in final image
4. **Pin base tags** — prefer digest or specific version, not only `latest`
5. **One process** per container; PID 1 should handle signals (tini/dumb-init if needed)
6. **.dockerignore** — exclude `.git`, `node_modules`, tests, secrets, local envs

### Node example

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S app && adduser -S app -G app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
USER app
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### Python example

```dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN adduser --disabled-password --no-create-home app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
USER app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Go example

```dockerfile
FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/app ./cmd/app

FROM gcr.io/distroless/static:nonroot
COPY --from=build /out/app /app
USER nonroot:nonroot
ENTRYPOINT ["/app"]
```

---

## .dockerignore

```
.git
node_modules
**/__pycache__
.env
.env.*
dist
coverage
*.md
Dockerfile*
docker-compose*.yml
```

---

## Compose

```yaml
services:
  api:
    build: .
    ports:
      - "8080:8000"
    environment:
      DATABASE_URL: postgres://app:app@db:5432/app
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      # The Python image above does not include curl.
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)"]
      interval: 10s
      timeout: 3s
      retries: 5

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    # Add a host port only when local tools must connect directly.
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  pgdata:
```

---

## Commands you'll use

```bash
docker build -t myapp:dev .
docker run --rm -p 8080:8000 --env-file .env myapp:dev
docker compose up --build
docker compose logs -f api
docker compose exec api sh
docker images
docker system df
docker builder prune   # careful
```

---

## Debugging

```bash
docker compose ps
docker inspect <cid>
docker logs <cid>
# shell in
docker run -it --entrypoint sh myapp:dev
```

Common fails:
- App binds `127.0.0.1` inside container → use `0.0.0.0`
- Wrong workdir / module path
- Missing runtime libs (use slim not alpine for glibc deps, or install)
- Permission denied on volume mounts (user id mismatch)

---

## Security & size

- Scan: `docker scout` / trivy when available
- Don't bake secrets into layers — runtime env or secret mounts
- Drop capabilities; read-only root FS when possible
- Distroless/alpine/slim over fat Ubuntu unless you need it

## Pitfalls

- Copying `.env` into image
- Running as root in prod
- `ADD` remote URLs when `curl` in RUN is clearer
- Huge contexts without `.dockerignore`
- `latest` tags in production compose without digests
- Publishing database/cache ports to the host when only sibling services need access
