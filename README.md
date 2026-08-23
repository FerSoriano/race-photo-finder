# 🏁 Race Photo Finder

> Runners find their race photos by typing their bib number. A local vision
> model reads the bib numbers off every photo after the race; the photos and
> detections are uploaded to an API; runners search by event and bib number
> and download what they want.

[![Status](https://img.shields.io/badge/status-active%20development%20(v0)-orange)]()
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)]()
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite%20%2B%20TS-blue)]()
[![Detection](https://img.shields.io/badge/detection-Ollama%20(qwen2.5vl)-black)]()

---

## ⚠️ Project status

> **Note:** Race Photo Finder is currently **Version 0 (pre-release / active
> development)**. The MVP works end-to-end against a local backend, but it
> is not deployed yet — no production domain, no payment flow. Expect the
> API and UI to keep changing. See [STATUS.md](STATUS.md) for the full
> done/pending/future breakdown.

---

## 🎯 Overview

A photographer shoots a race, runs bib detection locally with an offline
vision model, then uploads photos and detections to the API once back online.
Runners open the site, find their event, type their bib number, and get
their photos — free and unlimited for now; paid downloads are a later phase.

### Key capabilities (in progress)

- **📷 Offline bib detection** — `rpf detect` reads bib numbers off a folder
  of race photos with a local Ollama vision model, no internet required on
  race day.
- **☁️ Resumable upload pipeline** — `rpf upload` generates thumbnails and
  watermarked previews and pushes everything to the API, idempotent by
  SHA-256 so re-running after a failure is safe.
- **🔍 Fast bib search** — exact matches are a single indexed seek (0.165 ms
  measured over 1.5M detections); when nothing matches, trigram similarity
  suggests near numbers in case a digit was misread.
- **🔒 Private originals, public derivatives** — originals live in a private
  bucket and are only ever handed out through short-lived signed URLs; only
  thumbnails and watermarked previews are public.
- **🎨 A visual identity, not a placeholder theme** — dark-only "Volt sobre
  asfalto" palette, with the bib search itself styled as a race bib
  ("El Dorsal").
- **🛠️ Admin panel** — a separate `/admin` shell to create/edit/publish
  events, upload a cover image, and manage everything without touching the
  database by hand.

---

## 🛠️ Tech stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) + the `rpf` CLI,
  layered into routes/services/repositories, Postgres for data, MinIO
  (dev) / Cloudflare R2 (prod) for object storage.
- **Detection:** local [Ollama](https://ollama.com/) vision model
  (`qwen2.5vl:7b`) — runs offline on the photographer's laptop.
- **Frontend:** [React](https://react.dev/) + [Vite](https://vitejs.dev/) +
  TypeScript, Tailwind + shadcn/ui, TanStack Query. Reasoning in
  [frontend/README.md](frontend/README.md).
- **Package/env management:** [uv](https://docs.astral.sh/uv/) for Python.

---

## 🚀 Quick start

Requires Docker, [uv](https://docs.astral.sh/uv/) and
[Ollama](https://ollama.com/) with `qwen2.5vl:7b`.

```bash
make setup      # install deps, create .env
make up         # postgres + minio
make migrate    # create the schema
make api        # http://localhost:8000/docs
```

In another terminal, the frontend:

```bash
make front-setup   # npm install, create frontend/.env
make front         # http://localhost:5173
```

(`make dev-all` runs backend + frontend together in one terminal, useful for a
quick smoke test; `Ctrl+C` stops both.)

Then run the sample end to end:

```bash
make detect F=samples/photos E=test-event
make upload F=samples/photos E=test-event
docker compose exec -T postgres psql -U rpf -d rpf -c "UPDATE events SET is_published=true;"
curl -s "localhost:8000/v1/events/test-event/photos?bib=19131"
```

Or open `/admin` in the frontend, paste the admin key, and publish the event
from there instead of the `psql`/`curl` calls above.

`make help` lists everything else.

## 🗂️ Layout

```
backend/     FastAPI API + the `rpf` CLI (detect, upload, publish, cover)
frontend/    React + Vite + TypeScript SPA — see frontend/README.md
             includes the /admin panel (events, covers, publishing)
docs/        Architecture, data model, race-day runbook
samples/     Four test photos with known bib numbers
```

## ⚙️ How it works

1. **Race day** — shoot photos.
2. **Offline** — `rpf detect` reads bib numbers with a local Ollama model and
   writes a resumable `manifest.json`.
3. **Online** — `rpf upload` generates thumbnails and watermarked previews, then
   pushes everything through the admin API. Re-running is safe; photos are keyed
   by SHA-256.
4. **Publish** — `rpf publish --event <slug>` (or the `/admin` panel) flips
   the event to published and announce it.
5. **Runners** — search by bib. Exact matches are a single index seek; when
   nothing matches, trigram similarity suggests near numbers in case a digit was
   misread.

Originals are stored privately and handed out only through short-lived signed
URLs. Downloads are free and unlimited for now; that endpoint is the single
place a payment check will later go.

## 📚 Documentation

| Document | Contents |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System shape, storage model, measured search performance |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Tables, indexes, and why they look like that |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | Step-by-step race-day runbook |
| [CLAUDE.md](CLAUDE.md) | Conventions for working in this repo |
| [STATUS.md](STATUS.md) | What's done, what's pending, future phases |

## 🔧 Configuration

Copy `.env.example` to `.env`. Development defaults to filesystem storage;
production uses Cloudflare R2 (two buckets — originals private, derivatives
public). Switching providers is a config change: no application code names a
bucket or builds a URL.

Note: Postgres is exposed on host port **5433**, not 5432, to avoid colliding
with a locally installed Postgres.

## 🗺️ Roadmap

Not yet built, tracked in detail in [STATUS.md](STATUS.md):

- Payment gating for downloads (bank transfer first, provider not chosen).
- Download tracking (needed for the admin dashboard and for payment gating).
- Production deploy (Cloudflare R2 credentials, hosting).
- Event search/pagination once the catalogue grows past a handful of events.

## 🙏 Acknowledgements

Commit message style (Conventional Commits + gitmoji) is inspired by the
[FastAPI](https://github.com/fastapi/fastapi) repository.
