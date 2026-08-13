# Frontend rules

React + Vite + TypeScript, Tailwind + shadcn/ui. See `README.md` for setup,
commands and the reasoning behind the stack.

Agents do not commit or push. See the Git section in the root `CLAUDE.md`.

## Layering

- `pages/` -- one per route, owns data fetching (`useQuery`/`useMutation`)
  and page-level state (selection, URL search params). No presentational
  logic that could live in a reusable component.
- `components/` -- presentational, receive data and callbacks as props.
  `components/ui/` is shadcn/ui-managed; prefer `npx shadcn add <name>`
  over hand-writing a primitive that already exists there.
- `api/client.ts` -- the only place that calls `fetch`. Routes, response
  shapes and error handling live here, not in components.
- `types/api.ts` -- mirrors the backend's Pydantic schemas
  (`backend/src/rpf/schemas/`). If a backend schema changes, update this
  file to match; there is no codegen step.

## Conventions

- UI copy is Spanish; code, identifiers, comments stay English (root
  `CLAUDE.md`).
- `@/*` resolves to `src/*`. Defined in `vite.config.ts`, `tsconfig.json`
  *and* `tsconfig.app.json` -- shadcn's CLI reads path aliases from the root
  `tsconfig.json` only, so keep both in sync if the alias ever changes.
- Search state (the bib being searched) lives in the URL (`?bib=`), not in
  component state -- keep results shareable and back-button-friendly.
- Mobile-first for the public app. The primary audience is a runner on a
  phone on mobile data, minutes after a race, checking a link shared in a
  WhatsApp group.

## The admin panel (`/admin`)

A separate, desktop-first surface for the photographer: event CRUD,
publish/unpublish, and the cover image. It does not reuse `Layout` --
`components/admin/AdminLayout.tsx` is its own shell, and its pages
(`pages/admin/*`) are `React.lazy()`-loaded from `App.tsx` so none of it
reaches a runner's bundle.

**Mass photo ingest stays CLI-only (`rpf upload`) and always will.**
Detection runs offline against a local Ollama model (`rpf detect`); the API
server has no path to it. A photo uploaded from the browser would carry no
bib numbers and be unfindable by search, so the panel does not offer a photo
uploader -- only the single cover image, which needs no detection.

Auth is `X-Admin-Key` (`backend/src/rpf/api/deps.py`), the same header
`rpf upload` sends -- there is no separate scoped token yet. The key is
**never a build-time env var**: baking it into `VITE_*` would ship it to
every visitor's bundle. Instead `AdminRoute` shows a paste screen; the key
is verified against `GET /v1/admin/stats` before being written to
`localStorage` (`lib/adminAuth.ts`), with a 30-day expiry and a "Cerrar
sesión" button that clears it. Treat this as a real secret with a real
blast radius: it now lives in a browser, on the same origin as the public
site, and grants full ingest and deletion. Do not add a public page that
renders unescaped user-controlled HTML without weighing that risk.

## Before calling something done

```bash
npm run build   # tsc -b + vite build
npm run lint     # oxlint
```
