# Frontend

Not built yet. This document exists so the decision can be made quickly later,
with the reasoning already laid out.

## What it has to do

1. Browse published events.
2. Type a bib number, see matching photos fast.
3. Select one or several photos and download them.
4. Handle the "no exact match" case using the `similar_bibs` the API returns.

The audience is runners on a phone, on mobile data, minutes after a race, often
sharing the link in a WhatsApp group. Perceived speed and link previews matter
more than rich interactivity.

## Candidate stacks

### Next.js + TypeScript + Tailwind

Server-rendered event pages, so `/eventos/21k-gdl-2026` is indexable by Google
and produces a real preview card when shared. Deploys free on Vercel. Largest
ecosystem. Heaviest of the three, and couples you somewhat to Vercel's model.

**Pick this if** organic search ("fotos maratón Guadalajara") is expected to be
a meaningful source of traffic.

### React + Vite + TypeScript

A pure SPA served as static files from any host, including the R2 public bucket.
Simplest mental model, fastest to develop, no server runtime to operate. Costs
you SEO and social link previews unless you add prerendering.

**Pick this if** traffic comes from links you post yourself on social media,
which is the plan described in the workflow.

### Astro + React islands

Static event pages with an interactive island for the search box. Best raw
performance and good SEO, smaller ecosystem and fewer people know it.

**Pick this if** you want the SEO of Next with much less shipped JavaScript.

## Criteria to decide

| Question | Leads to |
| --- | --- |
| Will runners find events through Google? | Next.js or Astro |
| Is traffic driven only by your own social posts? | Vite SPA |
| Do you want zero server runtime to operate? | Vite SPA or Astro (static) |
| Will there be an admin panel with uploads later? | Next.js (API routes, auth) |

Given the stated workflow -- announcing on social media once photos are ready --
the Vite SPA is the cheapest thing that fully works. The moment you want to be
found by search, Next.js becomes the safer default.

## Constraints for whatever wins

- Thumbnails come from the public bucket's CDN domain; lazy-load them in a grid.
- Originals are **not** directly linkable. Download goes through
  `GET /v1/events/{slug}/photos/{id}/download`, which redirects to a short-lived
  signed URL. Do not cache or share those URLs.
- Previews are watermarked by design -- do not build a UI that implies otherwise.
- The API sets permissive CORS in dev and must be given explicit origins in prod.
