# Project status

Last updated: 2026-08-12

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
- Event cover images: optional `events.cover_url`, uploaded via
  `POST /v1/admin/events/{slug}/cover` and cleared via
  `DELETE /v1/admin/events/{slug}/cover` (admin/CLI only, no UI yet). Validated
  against the decoded image (jpg/png/webp, 5MB cap) rather than the declared
  content-type, stored in the public bucket at `events/{slug}/cover.{ext}`.
  `EventRead.cover_url` is `None` when unset, so the frontend's gradient
  placeholder stays the fallback.
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

- Stack chosen: React + Vite + TypeScript, Tailwind + shadcn/ui,
  react-router, TanStack Query. Reasoning in `frontend/README.md`.
- MVP built and verified end-to-end against the local backend
  (`samples/photos` seeded as `test-event`):
  - `EventsListPage` (`/`) — published events.
  - `EventDetailPage` (`/eventos/:slug`) — bib search, results split into
    "Tus fotos" (exact matches) and "¿Eres tú?" (possible matches: one
    search per `similar_bib`, rendered as real thumbnails, tapping one
    promotes it to the active search).
  - Multi-select across both sections, sticky selection bar, bulk download
    via `POST /v1/events/{slug}/photos/download`.
  - Photo preview dialog showing the watermarked `preview_url`.

### Pending

- **Visual design needs a real pass.** Currently running on shadcn/ui
  defaults with a single placeholder accent color — functional but generic,
  no identity. Needs actual design work (color, type, personality) before
  this is presentable to runners.
- **Selection UX: add a "cart" strip.** Right now the sticky bar only shows
  a count ("3 fotos seleccionadas"). Add a row of small thumbnails of the
  currently-selected photos (below the search results or in the sticky
  bar itself) so the runner can see at a glance which photos they've
  picked, not just how many.
- **"Deselect all" button, with a confirmation popup.** Add a way to clear
  the whole selection at once instead of unchecking photos one by one --
  guard it with a confirmation dialog so it isn't an accidental one-tap
  wipe of everything picked.

### Future phases

- Payment UI once a provider is chosen (see Backend future phases).
