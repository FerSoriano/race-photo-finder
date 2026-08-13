import { clearAdminKey, readAdminKey } from '@/lib/adminAuth'
import type {
  AdminStats,
  BulkDownloadResult,
  EventCreatePayload,
  EventRead,
  EventUpdatePayload,
  EventWithCount,
  PhotoSearchResult,
} from '@/types/api'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

// Mirrors Settings.max_bulk_download's default (backend/src/rpf/config.py).
// Only used to give the runner an early hint before they hit the real cap
// enforced server-side; the API's 422 response is the source of truth.
export const MAX_BULK_DOWNLOAD = 10

// Mirrors services/cover.py's MAX_COVER_BYTES and the formats it accepts.
// Early hint only -- the server's 422 is the source of truth.
export const MAX_COVER_BYTES = 5 * 1024 * 1024
export const COVER_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// FastAPI's `detail` is a string for a plain HTTPException but an array of
// {loc, msg, type} for a Pydantic 422. The public app never posts a
// validatable body, so this only starts mattering with the admin forms.
function detailMessage(body: unknown): string | null {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return (
      detail
        .map((e) => (e as { msg?: string }).msg)
        .filter(Boolean)
        .join('. ') || null
    )
  }
  return null
}

async function send(path: string, init: RequestInit): Promise<Response> {
  const res = await fetch(`${BASE_URL}${path}`, init)
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(detailMessage(body) ?? res.statusText, res.status)
  }
  return res
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await send(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
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

// --- Admin ---
//
// Every call below sends X-Admin-Key. The key is never a build-time env var
// (see lib/adminAuth.ts) -- it is pasted once by the operator and read from
// localStorage at request time.

function adminHeaders(override?: string): HeadersInit {
  const key = override ?? readAdminKey()
  return key ? { 'X-Admin-Key': key } : {}
}

// A 401 means the stored key is wrong or was rotated: drop it so the auth
// guard falls back to the paste screen instead of every panel query failing.
async function adminSend(
  path: string,
  init: RequestInit,
  keyOverride?: string,
): Promise<Response> {
  try {
    return await send(path, {
      ...init,
      headers: { ...adminHeaders(keyOverride), ...init.headers },
    })
  } catch (err) {
    if (err instanceof ApiError && err.status === 401 && !keyOverride) clearAdminKey()
    throw err
  }
}

async function adminJson<T>(
  path: string,
  init: RequestInit = {},
  keyOverride?: string,
): Promise<T> {
  const res = await adminSend(
    path,
    { ...init, headers: { 'Content-Type': 'application/json', ...init.headers } },
    keyOverride,
  )
  return res.json() as Promise<T>
}

// For 204 No Content -- res.json() would throw on an empty body.
async function adminVoid(path: string, init: RequestInit): Promise<void> {
  await adminSend(path, init)
}

// For multipart -- Content-Type is deliberately omitted so the browser sets
// it WITH the boundary parameter. Setting it by hand breaks the upload.
async function adminUpload<T>(path: string, form: FormData): Promise<T> {
  const res = await adminSend(path, { method: 'POST', body: form })
  return res.json() as Promise<T>
}

/** Probes a candidate key before it is ever persisted -- see AdminLoginPage. */
export function verifyAdminKey(key: string): Promise<AdminStats> {
  return adminJson('/v1/admin/stats', {}, key)
}

export function getAdminStats(): Promise<AdminStats> {
  return adminJson('/v1/admin/stats')
}

export function listAdminEvents(): Promise<EventWithCount[]> {
  return adminJson('/v1/admin/events')
}

export function getAdminEvent(slug: string): Promise<EventWithCount> {
  return adminJson(`/v1/admin/events/${encodeURIComponent(slug)}`)
}

export function createEvent(payload: EventCreatePayload): Promise<EventRead> {
  return adminJson('/v1/admin/events', { method: 'POST', body: JSON.stringify(payload) })
}

export function updateEvent(slug: string, payload: EventUpdatePayload): Promise<EventRead> {
  return adminJson(`/v1/admin/events/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteEvent(slug: string): Promise<void> {
  return adminVoid(`/v1/admin/events/${encodeURIComponent(slug)}`, { method: 'DELETE' })
}

export function uploadCover(slug: string, file: File): Promise<EventRead> {
  const form = new FormData()
  form.set('file', file)
  return adminUpload(`/v1/admin/events/${encodeURIComponent(slug)}/cover`, form)
}

// Note the asymmetry: unlike deleteEvent (204, removes the resource), this
// mutates a field and returns the updated EventRead -- both are correct for
// what they do, but it looks like an inconsistency at a glance.
export function deleteCover(slug: string): Promise<EventRead> {
  return adminJson(`/v1/admin/events/${encodeURIComponent(slug)}/cover`, { method: 'DELETE' })
}
