export function formatEventDate(iso: string | null): string | null {
  if (!iso) return null
  return new Date(iso).toLocaleDateString('es-MX', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

/** `12 de octubre de 2025 · Guadalajara`, skipping whichever part is missing. */
export function formatEventMeta(
  iso: string | null,
  location: string | null,
): string {
  return [formatEventDate(iso), location].filter(Boolean).join(' · ')
}
