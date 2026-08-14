# Race-day runbook

The end-to-end process, from shooting to announcing.

## 1. At the race — shoot

Nothing to do but take photos.

## 2. Still on site or at home — detect (offline)

Copy the memory card into a folder, one folder per event:

```bash
cp -r /Volumes/CARD/DCIM/* ~/races/21k-gdl-2026/
```

Make sure Ollama is running and the model is present:

```bash
ollama list | grep qwen2.5vl
```

Run detection:

```bash
uv --project backend run rpf detect ~/races/21k-gdl-2026 --event 21k-gdl-2026
```

This writes `~/races/21k-gdl-2026/manifest.json`, saving after **every** photo.
No internet needed.

- Interrupted? Re-run the same command — finished photos are skipped.
- A photo errored? It is recorded with the error and retried next run.
- Want to re-analyze everything (e.g. after changing the prompt)? Add `--force`.

Expect seconds per photo. A few hundred photos is a coffee break; leave it
running.

### Fixing detections by hand

`manifest.json` is plain JSON — open it and correct a bib the model misread
before uploading:

```json
{ "filename": "IMG_0421.jpg", "sha256": "…",
  "bibs": [{ "number": "19131", "is_uncertain": false }] }
```

## 3. At the office — upload (online)

```bash
uv --project backend run rpf upload \
  --event 21k-gdl-2026 \
  --manifest ~/races/21k-gdl-2026/manifest.json \
  --create-event --name "Medio Maratón Guadalajara 2026" \
  --api-url https://api.yourdomain.com \
  --admin-key "$RPF_ADMIN_KEY"
```

What happens per photo: thumbnail and watermarked preview are generated locally,
the original goes to the private bucket, derivatives to the public one, and the
bib numbers land in Postgres.

- Connection dropped? Re-run it. The CLI asks the server which hashes it already
  has and uploads only the rest.
- Check first without sending anything: add `--dry-run`.
- The event is created **unpublished**, so nothing is public yet.

## 4. Set a cover image (optional)

Gives the event a banner on the public listing instead of the frontend's
gradient placeholder:

```bash
uv --project backend run rpf cover 21k-gdl-2026 ~/races/21k-gdl-2026/cover.jpg \
  --api-url https://api.yourdomain.com \
  --admin-key "$RPF_ADMIN_KEY"
```

jpg/png/webp, 5MB max. Re-running it replaces the current cover. To remove it:

```bash
uv --project backend run rpf cover 21k-gdl-2026 --undo \
  --api-url https://api.yourdomain.com \
  --admin-key "$RPF_ADMIN_KEY"
```

## 5. Verify before announcing

```bash
curl "https://api.yourdomain.com/v1/events/21k-gdl-2026" \
     -H "X-Admin-Key: $RPF_ADMIN_KEY"
```

Confirm `photo_count` matches what you uploaded, then spot-check a bib you know
appears in a photo.

## 6. Publish

```bash
uv --project backend run rpf publish --event 21k-gdl-2026 \
  --api-url https://api.yourdomain.com \
  --admin-key "$RPF_ADMIN_KEY"
```

This flips `is_published` to true via `PATCH /v1/admin/events/{slug}`. Then
announce on social media.

Made a mistake and need to pull it back? `rpf publish --event <slug> --undo`.

## 7. When a runner cannot find their photos

1. Confirm the bib is right — they sometimes give the chip number instead.
2. Search the API directly. If `similar_bibs` comes back populated, the model
   misread a digit; fix the entry in the manifest and re-upload, or correct the
   row directly.
3. If the bib is genuinely absent, the number was never legible in any photo.

## Local development

```bash
make setup && make up && make migrate && make api
make detect F=samples/photos E=test-event
make upload F=samples/photos E=test-event
curl "localhost:8000/v1/events/test-event/photos?bib=19131"
```

The four sample photos have known answers — `21k-gdl-3.jpg` must yield
`19131, 6133, 13441`. That is the regression check for any change to the prompt
or the parser.
