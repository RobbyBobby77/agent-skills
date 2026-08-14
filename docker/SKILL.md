---
name: docker
description: >
  Write and debug Dockerfiles and Compose from the repo's actual runtime:
  multi-stage builds, image size, networking, volumes, healthchecks, and
  non-root production images. Use when containerizing an app, fixing a
  container, or authoring a compose stack. Do not use for Kubernetes-only
  cluster work unless a local Docker/Compose file is the artifact.
---

# Docker

Agents write a pretty Dockerfile for a stack the repo does not use, copy
`.env` into the image, and publish Postgres to the host. This skill exists
to prevent those.

## Related skills

| Need | Skill |
|------|-------|
| Tests that run inside the compose stack | `testing` |
| API the container exposes | `api` |
| Config files mounted into the container | `json-yaml` |

## Workflow

1. **Inspect** the existing Dockerfile/Compose, lockfile, start command, port, health endpoint, and `.dockerignore`.
2. **Match** the package manager and the runtime version already supported. Do not jump to a newer major.
3. **Build** with the smallest context. Secrets stay out of layers, build args, and git history.
4. **Run** as the final non-root user and hit the healthcheck or the primary command.
5. **Report** image size, published ports, user, and anything you could not boot.

**Hard rules**
- If a Dockerfile already exists, edit it. Do not start a parallel one.
- Multi-stage for anything with a compiler, bundler, or extra pip/npm build tools.
- Pin base tags (`3.12-slim`, digest if production). Never `latest` in a file you expect to last.
- The process listens on `0.0.0.0` inside the container.
- Do not publish database or cache ports to the host unless a local tool must connect.
- Do not copy `.env`, `.git`, or secrets into the image.
- Do not run `docker builder prune` or delete volumes unless asked.

---

## Inspect

```bash
ls -a Dockerfile* docker-compose*.yml compose*.yml .dockerignore 2>/dev/null
# runtime the repo already chose
head -n 20 package.json pyproject.toml go.mod Gemfile 2>/dev/null
```

Use `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` / `poetry.lock` /
`uv.lock` / `go.sum` that is actually present. Inventing `npm ci` in a pnpm
repo is a broken image.

---

## Dockerfile shape

Every production image:

1. **Builder stage** — toolchain + full install + build
2. **Runtime stage** — only the interpreter/OS bits the process needs, a non-root user, the artifact

Copy lockfiles **before** source so dependency layers cache.

### Node

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

Swap `npm ci` for `pnpm install --frozen-lockfile` or `yarn install --immutable` when that is the lockfile. Copy the matching lockfile only.

### Python

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
WORKDIR /app
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runner
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN adduser --disabled-password --no-create-home app
COPY --from=builder /install /usr/local
COPY --chown=app:app . .
USER app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

If the app needs build deps (gcc, libpq-dev), install them in **builder** only. Slim, not alpine, when the app needs glibc wheels.

### Go

```dockerfile
# syntax=docker/dockerfile:1
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

Exclude things that are not needed to *build* or *run*:

```
.git
.gitignore
**/.env
**/.env.*
**/__pycache__
node_modules
coverage
dist
*.pem
```

Do **not** blanket-ignore `*.md` (some builds copy `README` or license into the image, and docs-in-image is a real pattern). Do **not** ignore `Dockerfile*` or `compose*.yml` unless you know no stage `COPY`s them.

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
      # The Python image above does not include curl or wget.
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
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      timeout: 3s
      retries: 10
    # No host port. Sibling services use the hostname "db".

volumes:
  pgdata:
```

Healthchecks must use a binary that exists in *that* image. `depends_on` without `condition: service_healthy` only waits for start, not readiness.

---

## Debug in this order

The failure is usually bind address, missing file, missing shared lib, or user/volume permissions. Do not reshuffle the Dockerfile until you know which.

```bash
docker compose ps
docker compose logs --tail=200 api
docker inspect "$(docker compose ps -q api)" --format '{{.State.Status}} {{.State.ExitCode}} {{.Config.User}}'
docker compose exec api sh -c 'id; ls -l; ss -lnt || netstat -lnt'
# image that will not start:
docker run --rm -it --entrypoint sh myapp:dev
```

| Symptom | First check |
|---------|-------------|
| Connection refused from the host | Process bound `127.0.0.1` → `0.0.0.0`; published port is `host:container` |
| Module not found / wrong CMD | `WORKDIR`, package path, `CMD` vs lockfile start script |
| `error loading shared libraries` | alpine image + glibc wheel → switch runtime to slim or install the lib |
| Permission denied on a volume | container user uid vs host-owned mount; do not just `chmod 777` |
| Healthy in compose, 502 at the edge | healthcheck hits a path the app does not serve |
| Rebuild ignores code changes | context too big / copying from the wrong stage / leftover volume |

```bash
docker build -t myapp:dev .
docker run --rm -p 8080:8000 --env-file .env myapp:dev
docker compose up --build
docker images myapp:dev
```

Destructive: `docker builder prune`, `docker compose down -v` — ask first.

---

## Security and size

- Runtime env or secret mounts, never `ENV PASSWORD=` or `COPY .env`.
- Scan when the tool exists (`docker scout`, `trivy`).
- Distroless / alpine / slim over a kitchen-sink Ubuntu unless you need the extra packages.
- Read-only root filesystem when the app can live with a tmp volume.

---

## Verify

```text
[ ] Builds with the repo's lockfile
[ ] Final USER is not root
[ ] No secret file in `docker history` / later layers
[ ] Process reachable on the published port
[ ] Healthcheck uses a binary that exists
[ ] DB/cache not published unless requested
[ ] Image size reported
```
