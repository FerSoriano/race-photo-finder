---
name: db-migration
description: Create, review, apply or roll back an Alembic database migration. Use when changing SQLAlchemy models, adding a table/column/index/constraint, or when the app fails with a missing-column or missing-relation error.
---

# Database migrations

## The loop

```bash
# 1. Edit backend/src/rpf/db/models.py
# 2. Generate
make migration M="add orders table"
# 3. READ the generated file in backend/src/rpf/db/migrations/versions/
# 4. Apply
make migrate
# 5. Verify
docker compose exec -T postgres psql -U rpf -d rpf -c "\d+ orders"
```

Step 3 is not optional.

## What autogenerate does NOT detect

You must add these by hand — the initial migration is the worked example:

- **Extensions**: `op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")`
- **Raw-SQL indexes** such as the GIN trigram index:
  ```python
  op.execute(
      "CREATE INDEX ix_photo_bibs_number_trgm "
      "ON photo_bibs USING gin (bib_number gin_trgm_ops)"
  )
  ```
- Data backfills, `CHECK` constraints written as raw SQL, server-side defaults
  on existing rows.

Always write the matching `downgrade()`. Autogenerate cannot infer these, so it
will silently produce an incomplete rollback.

## Adding a NOT NULL column to a populated table

Three steps in one migration, or it fails on existing rows:

```python
op.add_column("photos", sa.Column("kind", sa.String(20), nullable=True))
op.execute("UPDATE photos SET kind = 'action'")
op.alter_column("photos", "kind", nullable=False)
```

## Rollback

```bash
cd backend && uv run alembic downgrade -1
cd backend && uv run alembic history
cd backend && uv run alembic current
```

## Connection details

The URL comes from `rpf.config` (i.e. `.env`), **not** from `alembic.ini` —
there are no credentials in that file, by design. If alembic cannot connect,
check `DATABASE_URL` and remember Postgres is on **host port 5433**.

## Project-specific invariants

- `photo_bibs.event_id` is denormalised from `photos.event_id` to keep the
  search a single index seek. Any new write path must populate it.
- `ix_photo_bibs_event_bib (event_id, bib_number)` is the index the core search
  depends on — do not drop or reorder its columns.
- `UNIQUE (event_id, sha256)` on `photos` is what makes uploads idempotent.
- Bib numbers are `varchar`, never integer.

After migrating, run `make test` — a broken model shows up there first.
