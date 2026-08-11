# Project status

Last updated: 2026-08-10

Tracks what's done, what's pending, and future phases. Split into Backend and
Frontend. See `CLAUDE.md` for the rule that keeps this current.

## Backend

### Done

- Layered FastAPI app: `api/routes`, `services`, `repositories`, `schemas`,
  `db`, `storage`, `detection`, `cli`.
- DB schema (`events`, `photos`, `photo_bibs`) with an initial Alembic
  migration.
- Bib detection via local Ollama vision model (`qwen2.5vl:7b`), writing a
  resumable `manifest.json` (`rpf detect`).
- Upload pipeline: thumbnails + watermarked previews, idempotent by
  SHA-256 (`rpf upload`).
- Storage abstraction: local filesystem for dev, S3/R2 for prod, with the
  private-originals / public-derivatives split enforced.
- Bib search: exact match via indexed seek (0.165 ms measured), trigram
  similarity fallback for near-misses (misread digits).
- Downloads: one signed URL per photo, plus
  `POST /v1/events/{slug}/photos/download` for a gallery selection (capped by
  `MAX_BULK_DOWNLOAD`, default 10). Both go through
  `services/download.py:link_for` — the one place the payment check will go.
  Signed URLs carry the original filename, so a batch does not land as UUIDs.
- Dev stack: Postgres (host port 5433) + MinIO via `make up` / `migrate` /
  `api`.
- Unit + integration test suite (config, derivatives, manifest, normalize,
  search, storage, API).
- Docs: `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/WORKFLOW.md`.

### Pending

- Production deploy configuration (R2 credentials, hosting, etc.) not yet
  set up.

### Future phases

- Payment gating for downloads (phase 2, not a current TODO). README already
  marks the single endpoint where this check will go; not implemented yet.
  Downloads are currently free and unlimited by design. First via bank
  transfer (`transferencia`), delivered by email or a download code —
  payment provider not chosen yet.
- ~~C/C++-accelerated search algorithm~~ — resolved: not needed. The
  Postgres indexed seek already measures 0.165 ms; see `CLAUDE.md`
  "Non-obvious facts".

## Frontend

### Done

- Nothing yet — `frontend/` has a README only, no code (per root
  `CLAUDE.md`, deliberately).

### Pending

- Choose the frontend stack.

### Future phases

- Event search, bib search UI, photo gallery with multi-select, download
  flow. The multi-select download has an API to call now: POST the selected
  photo ids and trigger the returned signed URLs client-side (browsers prompt
  once to allow multiple downloads).
- Payment UI once a provider is chosen (see Backend future phases).
