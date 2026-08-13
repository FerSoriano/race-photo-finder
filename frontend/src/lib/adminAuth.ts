import { useSyncExternalStore } from 'react'

const STORAGE_KEY = 'rpf.admin'
const TTL_MS = 30 * 24 * 60 * 60 * 1000

interface Stored {
  key: string
  expiresAt: number
}

// The X-Admin-Key never becomes a build-time env var (it would ship to every
// visitor's bundle). Instead the panel asks for it once and holds it here --
// a hard 30-day cap, not a refreshed session.
function read(): Stored | null {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as Stored
    if (typeof parsed.key !== 'string' || Date.now() > parsed.expiresAt) {
      localStorage.removeItem(STORAGE_KEY)
      return null
    }
    return parsed
  } catch {
    localStorage.removeItem(STORAGE_KEY)
    return null
  }
}

export function readAdminKey(): string | null {
  return read()?.key ?? null
}

const listeners = new Set<() => void>()
function notify() {
  for (const listener of listeners) listener()
}

export function saveAdminKey(key: string): void {
  const stored: Stored = { key, expiresAt: Date.now() + TTL_MS }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(stored))
  notify()
}

export function clearAdminKey(): void {
  localStorage.removeItem(STORAGE_KEY)
  notify()
}

function subscribe(onStoreChange: () => void): () => void {
  listeners.add(onStoreChange)
  window.addEventListener('storage', onStoreChange)
  return () => {
    listeners.delete(onStoreChange)
    window.removeEventListener('storage', onStoreChange)
  }
}

/** Same-tab writes go through the listener set; cross-tab logout arrives via
 * the native `storage` event -- both funnel through this one hook. */
export function useAdminKey(): string | null {
  return useSyncExternalStore(subscribe, readAdminKey)
}
