# Data model

Three tables. Defined in `backend/src/rpf/db/models.py`.

```
events ──1:N──► photos ──1:N──► photo_bibs
   └──────────────1:N──────────────┘
        (denormalised event_id)
```

## events

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `slug` | varchar(120) | unique, indexed. Used in URLs: `/eventos/21k-gdl-2026` |
| `name` | varchar(200) | |
| `event_date` | date | nullable |
| `location` | varchar(200) | nullable |
| `description` | text | nullable |
| `is_published` | bool | indexed. False = invisible to the public API |
| `created_at` | timestamptz | |

`is_published` lets photos be uploaded and checked before the social media
announcement. The public API 404s on unpublished events rather than 403-ing, so
an unannounced race is not discoverable by guessing slugs.

## photos

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK. Also the storage filename |
| `event_id` | uuid | FK → events, ON DELETE CASCADE, indexed |
| `original_filename` | varchar(255) | as it came off the camera |
| `sha256` | varchar(64) | **unique per event** — the idempotency key |
| `storage_key_original` | varchar(500) | private bucket |
| `storage_key_preview` | varchar(500) | public bucket |
| `storage_key_thumb` | varchar(500) | public bucket |
| `width`, `height` | int | of the original, nullable |
| `taken_at` | timestamptz | from EXIF, nullable. Used for ordering |
| `created_at` | timestamptz | |

Storage keys follow `events/{event_slug}/{original|preview|thumb}/{photo_id}.jpg`.
Keyed by photo id, not filename, so two events can hold the same `IMG_1234.jpg`
and nothing collides.

`UNIQUE (event_id, sha256)` is what makes re-running `rpf upload` safe.

## photo_bibs

One row per bib number detected in one photo. A photo with three runners has
three rows.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `photo_id` | uuid | FK → photos, CASCADE, indexed |
| `event_id` | uuid | FK → events, CASCADE. **Denormalised on purpose** |
| `bib_number` | varchar(16) | text, not int — leading zeros are meaningful |
| `is_uncertain` | bool | the model flagged a digit it was unsure of |
| `confidence` | float | nullable; the current model does not report one |
| `source` | varchar(16) | `model` or `manual` (hand corrections later) |
| `model_name` | varchar(80) | e.g. `qwen2.5vl:7b` — lets a re-detection be traced |
| `created_at` | timestamptz | |

### Indexes

| Index | Purpose |
| --- | --- |
| `ix_photo_bibs_event_bib (event_id, bib_number)` | the core search, single seek |
| `ix_photo_bibs_number_trgm` GIN | fuzzy "did you mean" fallback |
| `uq_photo_bibs_photo_number (photo_id, bib_number)` | no duplicate detections |

### Why `event_id` is duplicated here

The hot query is "photos of event X containing bib N". With `event_id` on this
table it is one index seek. Without it, every search would join to `photos` just
to filter by event. The cost is keeping the column in sync on insert — handled
in `repositories/photos.add_bibs`.

### Why `bib_number` is text

`0042` and `42` can both be worn at the same race, and a runner types what is
printed on their chest. Storing an integer would silently merge them.

## Not modelled yet

Orders, payments and download tokens. The design leaves room for them: originals
are already private, and every download already passes through one endpoint that
can check entitlement without touching anything else.
