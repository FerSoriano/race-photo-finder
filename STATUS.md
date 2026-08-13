# Project status

Last updated: 2026-08-12 (evening)

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
- Event publishing: `PATCH /v1/admin/events/{slug}` (partial update — a field
  left out of the request is untouched, `EventUpdate.model_dump(exclude_unset=True)`)
  and `rpf publish --event <slug>` / `--undo` on top of it. Closes the gap
  `docs/WORKFLOW.md` step 5 used to describe ("flip `is_published` to true")
  with no actual command behind it. Unpublishing only hides an event from the
  public routes (`PublishedEvent`, both event detail and photo search) — it is
  not a soft delete, the row and its photos are untouched and still reachable
  by the admin (`AnyEvent`).
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
- Event list ordering and search on `GET /v1/events`: `event_date DESC`
  ordering, `limit`/`offset`, and a `?q=` filter over name and location.
  The ordering is the backend's job by decision — the client must not sort.
  `?q=` is only needed once the catalogue passes ~200 events; below that the
  frontend filters what it already has. Drives the Frontend → Future phases
  item on event search and pagination.

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
- **Visual design pass — "Volt sobre asfalto".** The placeholder hue-35
  accent is gone; the app has an identity. Verified in the browser.
  - Palette: near-black ground (`asfalto`) with a single high-energy lime
    accent (`volt`) spent once per screen, plus amber (`warning`) for the
    detector's uncertain reads. Amber deliberately, never red — a near-miss
    is a recovery path, not an error. `accent` stays a neutral surface
    because shadcn uses it for every hover.
  - **Dark-only, by decision.** The light token block, `.dark` and
    `@custom-variant dark` were deleted rather than left as dead code. The
    dark ground is what makes the photos pop; there is no toggle and no
    place for one. Revisit that decision before reintroducing a second theme.
  - Type: Geist for body, **Archivo** for `--font-heading` (which was a
    no-op pointing at `--font-sans`), plus `tabular-nums` wherever digits
    carry meaning.
  - Signature element — **El Dorsal**: the bib search is not an input styled
    like a race bib, it is the bib. The same motif runs at three scales:
    the hero (`Bib`), the number badge on each photo (`BibBadge`), the
    header mark, and every empty state (`EmptyBib`).
- Layout shell (`Layout`) with a sticky header and a way back to the event
  list, a real 404 route, and OG/description/theme-color metadata so
  WhatsApp links render a preview card. `og:image` is a generated 1200×630
  `public/og.png`.
- `EventsListPage`: cards with cover art, loading skeletons matching the card
  shape, and designed empty/error states. Cover art uses `cover_url` when
  present and falls back to a gradient derived from the slug — also on image
  load failure — so an event without a photo still looks deliberate.
- `EventDetailPage`: hero-first layout with the bib search above the fold
  over the event cover, photo grid respecting real aspect ratios via
  `PhotoRead.width`/`height` (the old `aspect-square` cropped every portrait),
  `is_uncertain` surfaced on the tile, and grid skeletons.
- `PossibleMatches` redesigned as a recovery path: a real, prominent
  "Sí, soy el {bib}" button instead of an underlined text link.
- `SelectionBar`: thumbnail strip of the selected photos with per-photo
  removal, a `3 / 10` cap indicator that warns before the server rejects,
  "Quitar todo" behind an `alert-dialog`, and a toast confirming a download
  fired. Selection is keyed by photo id in a `Map` holding the whole photo,
  because a selected photo can come from a "¿Eres tú?" section the page
  never fetched itself.
- Scaffold residue removed: `vite-scaffold` title, shadcn favicon,
  `icons.svg`, and the `badge`/`card`/`input` primitives left unused by the
  redesign. `SearchBox` was superseded by `Bib`.

### Pending

- **`VITE_SITE_URL` must be set at deploy time.** It builds the absolute
  `og:image` URL in `index.html`; WhatsApp will not render a preview card
  from a relative one. Falls back to the dev-server origin when unset.
- **Pagination is still unused.** `searchPhotos` accepts `limit`/`offset`
  and the client never sends them, so a bib with many photos renders all at
  once.
- **Selection is lost on reload** — it lives in page state, not the URL.

### Future phases

- Payment UI once a provider is chosen (see Backend future phases).
- **Background pattern on the hero.** A dot pattern behind the hero/header,
  pure CSS via `radial-gradient` — no external library, this is native CSS.
  Scope it to the hero only, never the whole page: the photo grid is the
  content, and a full-page texture would compete with it.
- **Event search and pagination on `EventsListPage`.** Today only a single
  test event is listed. Events must render newest-first, and once the
  catalogue grows (target: 100+ events) the home page should show only the
  latest 10 plus a search input filtering by name, city or date.
  - Filtering can stay client-side while the total is under ~200; past that
    it moves to the backend behind `?q=`.
  - **Date DESC ordering must come from the backend, not from sorting in the
    client.** Needs the `GET /v1/events` change tracked in Backend →
    Future phases.
- **Global footer in the layout shell.** Sections: "Quiénes somos"
  (`/about`), social links (Instagram, Facebook, TikTok), privacy notice and
  terms of use (`/privacidad`, `/terminos`), and copyright. This phase only
  wires the links — the static pages themselves are not built yet. Keep the
  styling discreet so it does not compete with the main content.
