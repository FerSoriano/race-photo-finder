# Backend rules

FastAPI + SQLAlchemy + Postgres, plus the `rpf` CLI. Package root:
`backend/src/rpf/`.

Agents do not commit or push -- including generated migrations. See the Git
section in the root `CLAUDE.md`.

## Layering -- the rule that matters most

```
api/routes  ->  services  ->  repositories  ->  db
                    \-> storage (via the StorageBackend protocol)
```

Dependencies point one way only:

- **Routes** parse input, call one service, return a schema. No SQLAlchemy
  queries, no business rules, no direct storage calls.
- **Services** hold the rules and orchestrate. They never import `fastapi` and
  never raise `HTTPException`.
- **Repositories** hold queries. They never import `fastapi` or schemas.

This exists so the API and the CLI can share the same logic. Break it and the
next ingest path silently forks the definition of "a photo is in the system".

## Storage -- a security boundary

All file I/O goes through the `StorageBackend` protocol (`storage/base.py`).

**Outside `rpf/storage/` you must never**: import `boto3`, name a bucket,
build a URL by hand, or touch the filesystem for photo data.

Two buckets, and the split is load-bearing:

| Visibility | Bucket | Holds | Reachable by |
| --- | --- | --- | --- |
| `public` | `S3_PUBLIC_BUCKET` | thumbs, previews | anyone, via the CDN domain |
| `private` | `S3_BUCKET` | **originals** | only a signed URL the API issues |

R2 grants public access per bucket -- attaching a custom domain exposes
everything in it, and there is no per-prefix switch. Originals therefore need a
bucket of their own. `GET /v1/events/{slug}/photos/{id}/download` is the single
choke point where the future payment check goes; keep it that way.

`LocalStorage` does **not** enforce this split -- everything under `/media` is
readable. Test the public/private boundary against MinIO, never against the
local backend.

`config.Settings` refuses to start under `ENVIRONMENT=prod` with local storage,
a default admin key, or a shared bucket. Do not weaken those checks to make a
deploy go through -- each one guards against a silent, expensive failure.

## Detection

`detection/` sits behind the `BibDetector` protocol so the Ollama model can be
replaced (YOLO + CRNN, PaddleOCR) without touching the CLI or services. The
prompt and JSON parsing in `ollama_detector.py` are carried over from the
original prototype and are verified against `samples/photos` -- if you change
them, re-run `rpf detect` and confirm `21k-gdl-3.jpg` still yields
`19131, 6133, 13441`.

Model output is never trusted raw: `normalize.py` strips the `?` uncertainty
marker, drops implausible lengths, and preserves leading zeros (bib `0042` is
printed that way on the chest).

## Database

- Schema changes: edit `db/models.py`, then `make migration M="..."`, then read
  the generated file. Autogenerate does **not** detect extensions
  (`pg_trgm`) or raw-SQL indexes (the GIN trigram index) -- add those by hand.
- `photo_bibs.event_id` is denormalised from `photos.event_id` on purpose: it
  makes the search a single seek on `ix_photo_bibs_event_bib`. Keep it in sync
  when inserting.
- Fuzzy bib matching uses the `%` operator, not `similarity() > x` -- only `%`
  can use the GIN index. Its threshold is a GUC, set transaction-locally so it
  cannot leak across pooled connections.

## Style

- Type hints on every function. `from __future__ import annotations` at the top.
- Pydantic schemas at every I/O boundary; never return an ORM object from a route.
- Secrets come from `config.Settings` only. No `os.environ` reads scattered around.
- `make lint && make test` before calling anything done.

## Tests

`tests/unit/` must run with no database and no network. Anything needing
Postgres or MinIO goes in `tests/integration/` and is marked
`@pytest.mark.integration` (excluded from `make test` by default).
