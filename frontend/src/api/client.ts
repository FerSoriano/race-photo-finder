import type {
  BulkDownloadResult,
  EventRead,
  EventWithCount,
  PhotoSearchResult,
} from '@/types/api'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

// Mirrors Settings.max_bulk_download's default (backend/src/rpf/config.py).
// Only used to give the runner an early hint before they hit the real cap
// enforced server-side; the API's 422 response is the source of truth.
export const MAX_BULK_DOWNLOAD = 10

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(body?.detail ?? res.statusText, res.status)
  }
  return res.json() as Promise<T>
}

export function getEvents(): Promise<EventRead[]> {
  return request('/v1/events')
}

export function getEvent(slug: string): Promise<EventWithCount> {
  return request(`/v1/events/${encodeURIComponent(slug)}`)
}

export function searchPhotos(
  slug: string,
  bib: string,
  opts?: { limit?: number; offset?: number },
): Promise<PhotoSearchResult> {
  const params = new URLSearchParams({ bib })
  if (opts?.limit) params.set('limit', String(opts.limit))
  if (opts?.offset) params.set('offset', String(opts.offset))
  return request(`/v1/events/${encodeURIComponent(slug)}/photos?${params}`)
}

export function requestBulkDownload(
  slug: string,
  photoIds: string[],
): Promise<BulkDownloadResult> {
  return request(`/v1/events/${encodeURIComponent(slug)}/photos/download`, {
    method: 'POST',
    body: JSON.stringify({ photo_ids: photoIds }),
  })
}
