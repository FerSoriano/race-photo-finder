---
name: dev-stack
description: Bring up, check or tear down the local development stack (Postgres, MinIO, the FastAPI server). Use when asked to start/stop the app, run the API locally, reset the local database or storage, or when a command fails with a connection error to Postgres or MinIO.
---

# Local development stack

## Start everything

```bash
make setup     # uv sync + create .env from .env.example if missing
make up        # postgres + minio, waits until postgres is ready
make migrate   # alembic upgrade head
make api       # uvicorn with reload on :8000
```

`make dev` chains all four.

## Check state before assuming anything is broken

```bash
docker compose ps                       # both containers healthy?
curl -s localhost:8000/health/ready     # API + DB reachable?
docker compose logs --tail=30 postgres
```

## Facts that cause confusing failures

- **Postgres is on host port 5433**, not 5432. A locally installed Postgres
  usually holds 5432 and will answer instead, producing
  `role "rpf" does not exist`. If you see that error, something is pointing at
  the wrong port.
- MinIO: API on `:9000`, console on `:9001` (`minioadmin` / `minioadmin`).
- Two buckets exist: `race-photos-private` (originals) and
  `race-photos-public` (thumbs, previews). `minio-init` creates them and exits —
  a stopped `minio-init` container is normal, not a failure.

## Switching storage backend

Development defaults to `STORAGE_BACKEND=local` (files under
`backend/var/storage`, served at `/media`).

To exercise the real S3 path — required whenever you touch `rpf/storage/` —
set in `.env`:

```
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=http://localhost:9000
S3_REGION=us-east-1
S3_BUCKET=race-photos-private
S3_PUBLIC_BUCKET=race-photos-public
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_PUBLIC_BASE_URL=http://localhost:9000/race-photos-public
```

Restart the API afterwards — settings are cached per process.

## Reset

```bash
docker compose exec -T postgres psql -U rpf -d rpf -c "DELETE FROM events;"  # cascades
docker compose exec -T minio mc rm --recursive --force local/race-photos-public
make clean          # local storage + __pycache__
docker compose down -v   # nuclear: drops the volumes too
```

## Smoke test

```bash
make detect F=samples/photos E=test-event
make upload F=samples/photos E=test-event
docker compose exec -T postgres psql -U rpf -d rpf -c "UPDATE events SET is_published=true;"
curl -s "localhost:8000/v1/events/test-event/photos?bib=19131"
```

Must return exactly one photo, `21k-gdl-3.jpg`.
