# Architecture

## Shape

```
  Laptop (race day, offline)          Server                     Runner
  ──────────────────────────          ──────                     ──────
  photos/                             FastAPI  ──► Postgres      browser
    │                                    │         (metadata)       │
    ▼                                    │                          │
  rpf detect ──► manifest.json           ├──► public bucket ──► CDN ┘
    (Ollama qwen2.5vl:7b)                │    thumbs, previews
    │                                    │
    ▼                                    └──► private bucket
  rpf upload ──── HTTPS + X-Admin-Key ──►      originals (signed URLs only)
```

Detection happens on the laptop, never on the server: the vision model is slow
and GPU-hungry, and the photographer already has the photos locally. The server
only stores and searches.

## Backend layers

```
api/routes  ->  services  ->  repositories  ->  db
                    \-> storage (StorageBackend protocol)
```

One direction only. The point is that `rpf upload` and the API share the same
service functions, so there is a single definition of what ingesting a photo
means. Details and enforcement: `backend/CLAUDE.md`.

## Storage: two buckets

| Bucket | Contents | Access |
| --- | --- | --- |
| `S3_PUBLIC_BUCKET` | thumbs, previews (watermarked) | public, via CDN domain |
| `S3_BUCKET` | originals | private; signed URLs only |

Cloudflare R2 grants public access **per bucket** -- attaching a custom domain
publishes everything inside it, with no per-prefix control. Since the paid
download model depends on originals being unreachable, they need their own
bucket. Two routes open that door -- one photo, or a selected batch -- but both
end in `services/download.py:link_for`, which is the only code that mints a
signed URL for an original and therefore the only place a future payment check
has to go.

R2 was chosen because egress is free. A runner downloading 6 MB photos costs
nothing, which is what makes the free launch phase affordable.

Everything goes through the `StorageBackend` protocol, so the provider is a
`.env` change: `LocalStorage` for development, `S3Storage` for MinIO, R2, B2 or
S3. No application code names a bucket or builds a URL.

## Data model

See `DATA_MODEL.md`. The one design decision worth restating: `photo_bibs`
carries a denormalised `event_id` so the search never joins to filter by event.

## Search performance — closing the C/C++ question

The original plan carried a TODO about implementing the search in C or C++ for
speed. **Measured, that is not needed.**

With 1.5M detections across 20 events (far beyond a real race weekend), the core
query — every photo of one event containing one bib — runs as pure index scans:

```
Nested Loop (actual time=0.101..0.102 rows=1)
  -> Index Scan using ix_photo_bibs_event_bib on photo_bibs
       Index Cond: (event_id = ... AND bib_number = '19131')
  -> Index Scan using photos_pkey on photos
Execution Time: 0.165 ms
```

0.165 ms, 10 buffers touched. A B-tree on `(event_id, bib_number)` is already
O(log n); a native implementation would compete for microseconds inside a
request whose real cost is elsewhere.

**Where the latency actually is**, in order:

1. Downloading thumbnails — dozens of images per result page. Fixed by small
   thumbs (400 px) on a CDN, not by a faster query.
2. TLS + network round trips from a phone on mobile data.
3. The query. Negligible.

So the performance work belongs in image delivery: CDN caching, correct
`Cache-Control`, lazy loading, and possibly AVIF/WebP thumbs later.

Detection is the genuinely slow step (seconds per photo, local vision model),
but it runs offline on the laptop and never blocks a runner.

## Fuzzy matching

OCR misreads a digit sometimes. When the exact search returns nothing, a
`pg_trgm` similarity query suggests near numbers so the UI can ask "did you mean
19131?" rather than dead-ending.

Threshold is 0.3: one wrong digit in a 5-digit bib scores 0.333, while unrelated
numbers score below 0.15. It uses the `%` operator rather than `similarity() > x`
because only `%` can be served by the GIN index (verified: the planner uses
`BitmapAnd` over the trigram and event indexes; ~22 ms on 1.5M rows). It runs
only on the empty-result path.

## API

```
GET  /health                                    liveness
GET  /health/ready                              readiness (checks the DB)
GET  /v1/events                                 published events
GET  /v1/events/{slug}                          event + photo count
GET  /v1/events/{slug}/photos?bib=19131         the core search
GET  /v1/events/{slug}/photos/{id}/download     302 to a signed original
POST /v1/events/{slug}/photos/download          signed originals for a selection
                                                (<= MAX_BULK_DOWNLOAD, default 10)

POST /v1/admin/events                           X-Admin-Key
GET  /v1/admin/events/{slug}/photos/hashes      X-Admin-Key (upload skip list)
POST /v1/admin/events/{slug}/photos             X-Admin-Key (ingest)
```

No runner accounts in phase 1 — search is public by event + bib. Unpublished
events return 404 to the public API, so photos can be uploaded before the
announcement.

## Idempotency

Photos are keyed by `(event_id, sha256)`. `rpf upload` first asks the server for
the hashes it already has, skips those, and the server re-checks on ingest. A
dropped connection mid-upload is fixed by re-running the same command.

The server verifies the client's declared sha256 against the received bytes, so
a truncated upload cannot claim an identity it does not have.

## Production guardrails

`config.Settings` refuses to boot with `ENVIRONMENT=prod` if any of these hold
(each is a mistake that would otherwise be silent and expensive):

| Rejected | Why |
| --- | --- |
| `STORAGE_BACKEND=local` | container filesystems are ephemeral — every photo would be lost on the next deploy |
| `ADMIN_API_KEY` left at its default | it is the only thing guarding photo ingest |
| `S3_BUCKET == S3_PUBLIC_BUCKET` | originals would become publicly downloadable |

Migrations are run as a deploy step, not on container start, so two replicas
booting together cannot race each other.

## Known gaps

- CORS is wide open unless `ENVIRONMENT=prod`; real origins must be pinned
  before launch.
- No rate limiting on the public search yet.
- `LocalStorage` does not enforce public/private separation — dev only.
- Derivatives are generated synchronously during upload. Fine for hundreds of
  photos; a job queue is the answer if a race ever produces thousands.
