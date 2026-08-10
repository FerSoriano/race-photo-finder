---
name: add-endpoint
description: Add a new endpoint to the FastAPI backend following the project's layered pattern. Use when asked to add an API route, expose new data over HTTP, or extend the admin ingest API.
---

# Adding an endpoint

Follow the layering. Dependencies point one way:

```
api/routes  ->  services  ->  repositories  ->  db
                    \-> storage (StorageBackend protocol)
```

## Order of work

### 1. Schema — `schemas/<area>.py`

Pydantic models for request and response. Never return an ORM object from a
route.

```python
class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    total: int
```

### 2. Repository — `repositories/<area>.py`

Queries only. No `fastapi` imports, no schemas, no business rules.

```python
def get_by_id(db: Session, order_id: uuid.UUID) -> Order | None:
    return db.get(Order, order_id)
```

### 3. Service — `services/<area>.py`

The rules. No `fastapi` import, and **never** raise `HTTPException` — return a
value or raise a domain error, so the CLI can call it too.

### 4. Route — `api/routes/<area>.py`

Parse input, call one service, return a schema. Use the shared dependencies in
`api/deps.py` rather than re-deriving them:

| Dependency | Gives you |
| --- | --- |
| `DbSession` | a request-scoped session, committed on success |
| `Storage` | the configured `StorageBackend` |
| `AppSettings` | `Settings` |
| `PublishedEvent` | the event from `{slug}`, 404 if missing or unpublished |
| `AnyEvent` | same but reaches unpublished events (admin) |
| `AdminGuard` | put in the router's `dependencies=[...]` to require X-Admin-Key |

```python
@router.get("/{slug}/orders", response_model=list[OrderRead])
def list_orders(event: PublishedEvent, db: DbSession) -> list[OrderRead]:
    return [OrderRead.model_validate(o) for o in order_repo.list_for(db, event.id)]
```

### 5. Register it — `main.py`

```python
app.include_router(orders.router)
```

### 6. Test — `tests/`

Unit tests must not need a database or network. Anything requiring Postgres or
MinIO goes in `tests/integration/` marked `@pytest.mark.integration`.

## Rules specific to this API

- **Public routes** use `PublishedEvent`. Unpublished events must 404, not 403 —
  an unannounced race should not be discoverable by guessing slugs.
- **Admin routes** live under `/v1/admin` on a router carrying
  `dependencies=[AdminGuard]`. Never hand-roll the key check.
- **Never expose `storage_key_original`** in a response schema. Originals are
  private; they leave only through the download endpoint's signed URL. That
  endpoint is where the future payment check goes.
- Photo URLs come from `storage.url(key, visibility=...)`. Never build one by
  hand and never import `boto3` outside `rpf/storage/`.
- Public list endpoints need `limit`/`offset` with a capped `limit`.

## Finish

```bash
make lint && make test
```

Then check the route in the OpenAPI docs at `localhost:8000/docs`.
