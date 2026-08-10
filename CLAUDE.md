# Race Photo Finder

A web app where runners find their race photos by typing their bib number.

Photographer's workflow: shoot the race → run local bib detection on a laptop
(offline, Ollama vision model) → back at the office, upload photos and
detections to the API → announce on social media that photos are ready.

Free and unlimited at first; paid downloads come later.

> Product vision and long-term intent live in `CLAUDE.local.md` (Spanish, not
> checked in). This file is the operational contract for working in the repo.

## Layout

```
backend/     FastAPI API + `rpf` CLI. See backend/CLAUDE.md before editing.
frontend/    Stack not chosen yet. README only -- do not add code.
docs/        Architecture and data model.
samples/     Four test photos with known bib numbers.
.claude/     Skills and permissions.
```

## Language

**English everywhere** -- code, comments, docstrings, docs, commit messages,
identifiers. The product UI will be Spanish; that is a translation concern, not
a source-code one.

## Commands

Run from the repo root:

```bash
make setup      # install deps, create .env
make up         # start postgres + minio
make migrate    # apply migrations
make api        # run the API with reload
make test       # unit tests
make lint       # ruff check + format check
make fmt        # auto-fix
make help       # everything else
```

`uv` manages Python; the venv lives at `backend/.venv`. Never call `pip`, never
edit `.venv/`, never activate a venv manually -- prefix with `uv run`.

## Conventions

- Never commit `.env`, credentials, or bucket keys. `.env.example` is the
  template and must stay in sync when a setting is added.
- Migrations are generated (`make migration M="..."`), then **reviewed by hand**
  -- autogenerate misses extensions, raw-SQL indexes and data changes.
- Commit messages: imperative mood, present tense (`Add bib search endpoint`).
- Before declaring work done: `make lint && make test`.

## Non-obvious facts

- **Postgres runs on host port 5433**, not 5432 -- a locally installed Postgres
  usually owns 5432 and would silently shadow the container.
- **Two object-storage buckets, deliberately.** Originals are private; only
  thumbs and previews are public. See `backend/CLAUDE.md` -- this is a security
  boundary, not a preference.
- The bib search is a single indexed seek (0.165 ms measured over 1.5M
  detections). If search feels slow, the cause is image delivery, not the query.
