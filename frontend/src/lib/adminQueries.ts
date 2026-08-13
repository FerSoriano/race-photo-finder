// Namespaced under 'admin' so a single invalidateQueries({queryKey: adminKeys.all})
// refreshes the whole panel, and these can never collide with the public keys
// ['events'] / ['event', slug] / ['photos', slug, bib] used elsewhere.
export const adminKeys = {
  all: ['admin'] as const,
  stats: ['admin', 'stats'] as const,
  events: ['admin', 'events'] as const,
  event: (slug: string) => ['admin', 'event', slug] as const,
}
