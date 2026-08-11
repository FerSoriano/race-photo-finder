# Frontend

The runner-facing web app: browse a race event, search photos by bib number,
select the ones that are yours, download them.

## Stack

React + Vite + TypeScript, Tailwind + shadcn/ui, react-router for `/` and
`/eventos/:slug`, TanStack Query for API calls.

Chosen over Next.js/Astro because traffic comes from links the photographer
posts on social media after a race, not from organic search -- a plain SPA is
the cheapest thing that fully works. Revisit this if discoverability via
Google search ever becomes a goal; see `docs/ARCHITECTURE.md` in the repo
root for the API this app talks to.

## Setup

```bash
npm install
cp .env.example .env   # VITE_API_BASE_URL, defaults to http://localhost:8000
npm run dev
```

Requires the backend running locally (`make up && make migrate && make api`
from the repo root) with at least one published event to see anything on the
home page.

## Commands

```bash
npm run dev       # dev server
npm run build     # typecheck (tsc -b) + production build
npm run lint       # oxlint
npm run preview   # preview a production build
```

## Structure

```
src/
  api/         typed fetch client (getEvents, getEvent, searchPhotos, requestBulkDownload)
  types/       types mirroring the backend's Pydantic schemas
  pages/       EventsListPage (/), EventDetailPage (/eventos/:slug)
  components/  SearchBox, PhotoGrid, PhotoCard, PossibleMatches, SelectionBar
  components/ui/  shadcn/ui primitives
  lib/         query client, download helper, cn()
```

`@/*` resolves to `src/*` (configured in `vite.config.ts` and both
`tsconfig.json` / `tsconfig.app.json` -- shadcn's CLI only reads the root
`tsconfig.json` for path aliases, so both files must agree).

## Conventions

- UI copy is Spanish (root `CLAUDE.md`); code, identifiers and comments stay
  English.
- Mobile-first: the audience is runners on a phone, on mobile data, minutes
  after a race.
- The search bib lives in the URL (`?bib=19131`), not component state, so
  results are shareable and survive the back button.
- No admin/upload UI here -- ingest is CLI-only (`rpf upload`) and stays
  that way; the `X-Admin-Key` routes are not a frontend concern.
- Previews (`preview_url`) are watermarked by design; never build UI that
  implies otherwise. Downloads only ever come from a signed URL returned by
  the API, never a direct storage link.
