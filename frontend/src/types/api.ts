export interface EventRead {
  id: string
  slug: string
  name: string
  event_date: string | null
  location: string | null
  description: string | null
  cover_url: string | null
  is_published: boolean
}

export interface EventWithCount extends EventRead {
  photo_count: number
}

export interface BibRead {
  number: string
  is_uncertain: boolean
}

export interface PhotoRead {
  id: string
  filename: string
  thumb_url: string
  preview_url: string
  width: number | null
  height: number | null
  taken_at: string | null
  bibs: BibRead[]
}

export interface PhotoSearchResult {
  event_slug: string
  bib: string
  total: number
  photos: PhotoRead[]
  similar_bibs: string[]
}

export interface BulkDownloadRequest {
  photo_ids: string[]
}

export interface PhotoDownloadLink {
  id: string
  filename: string
  url: string
}

export interface BulkDownloadResult {
  event_slug: string
  expires_in: number
  photos: PhotoDownloadLink[]
}

export interface AdminStats {
  events_total: number
  events_published: number
  events_draft: number
  photos_total: number
}

export interface EventCreatePayload {
  slug: string
  name: string
  event_date?: string | null
  location?: string | null
  description?: string | null
  is_published?: boolean
}

// Every field optional: an omitted field is left untouched by the backend's
// EventUpdate.model_dump(exclude_unset=True). An explicit null clears it.
export type EventUpdatePayload = Partial<Omit<EventCreatePayload, 'slug'>>
