# Race Photo Finder

Runners find their race photos by typing their bib number.

A local vision model reads the bib numbers off every photo after the race; the
photos and detections are uploaded to an API; runners search by event and bib
number and download what they want.

## Quick start

Requires Docker, [uv](https://docs.astral.sh/uv/) and
[Ollama](https://ollama.com/) with `qwen2.5vl:7b`.

```bash
make setup      # install deps, create .env
make up         # postgres + minio
make migrate    # create the schema
make api        # http://localhost:8000/docs
```

Then, in another terminal, run the sample end to end:

```bash
make detect F=samples/photos E=test-event
make upload F=samples/photos E=test-event
docker compose exec -T postgres psql -U rpf -d rpf -c "UPDATE events SET is_published=true;"
curl -s "localhost:8000/v1/events/test-event/photos?bib=19131"
```

`make help` lists everything else.

## Layout

```
backend/     FastAPI API + the `rpf` CLI (detect, upload)
frontend/    Stack not chosen yet — see frontend/README.md
docs/        Architecture, data model, race-day runbook
samples/     Four test photos with known bib numbers
```

## How it works

1. **Race day** — shoot photos.
2. **Offline** — `rpf detect` reads bib numbers with a local Ollama model and
   writes a resumable `manifest.json`.
3. **Online** — `rpf upload` generates thumbnails and watermarked previews, then
   pushes everything through the admin API. Re-running is safe; photos are keyed
   by SHA-256.
4. **Publish** — flip the event to published and announce it.
5. **Runners** — search by bib. Exact matches are a single index seek; when
   nothing matches, trigram similarity suggests near numbers in case a digit was
   misread.

Originals are stored privately and handed out only through short-lived signed
URLs. Downloads are free and unlimited for now; that endpoint is the single
place a payment check will later go.

## Documentation

| Document | Contents |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System shape, storage model, measured search performance |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Tables, indexes, and why they look like that |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | Step-by-step race-day runbook |
| [CLAUDE.md](CLAUDE.md) | Conventions for working in this repo |

## Configuration

Copy `.env.example` to `.env`. Development defaults to filesystem storage;
production uses Cloudflare R2 (two buckets — originals private, derivatives
public). Switching providers is a config change: no application code names a
bucket or builds a URL.

Note: Postgres is exposed on host port **5433**, not 5432, to avoid colliding
with a locally installed Postgres.
