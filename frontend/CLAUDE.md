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
- No admin/upload UI. Ingest is CLI-only (`rpf upload`, `X-Admin-Key`
  routes) and stays that way.
- Mobile-first. The primary audience is a runner on a phone on mobile data,
  minutes after a race, checking a link shared in a WhatsApp group.

## Before calling something done

```bash
npm run build   # tsc -b + vite build
npm run lint     # oxlint
```
