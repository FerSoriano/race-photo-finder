import { useEffect, useMemo, useState } from 'react'
import type { PhotoRead } from '@/types/api'
import { PhotoCard, PhotoCardSkeleton } from '@/components/PhotoCard'

interface PhotoGridProps {
  photos: PhotoRead[]
  selected: ReadonlyMap<string, PhotoRead>
  onToggleSelect: (photo: PhotoRead) => void
  highlightBib?: string
}

/**
 * Mirrors Tailwind's `sm` and `lg`. This is the one place a breakpoint lives in
 * TS instead of a class -- keep it in sync if the theme's breakpoints change.
 */
const BREAKPOINTS = [
  { query: '(min-width: 1024px)', columns: 4 }, // lg
  { query: '(min-width: 640px)', columns: 3 }, // sm
] as const

const MOBILE_COLUMNS = 2

/** Matches `PhotoCard`'s `aspect-3/4` fallback for a photo without dimensions. */
const FALLBACK_RATIO = 4 / 3

function readColumnCount(): number {
  for (const breakpoint of BREAKPOINTS) {
    if (window.matchMedia(breakpoint.query).matches) return breakpoint.columns
  }
  return MOBILE_COLUMNS
}

function useColumnCount(): number {
  const [count, setCount] = useState(readColumnCount)

  useEffect(() => {
    const lists = BREAKPOINTS.map((b) => window.matchMedia(b.query))
    const onChange = () => setCount(readColumnCount())
    lists.forEach((list) => list.addEventListener('change', onChange))
    onChange()
    return () => lists.forEach((list) => list.removeEventListener('change', onChange))
  }, [])

  return count
}

/**
 * Spreads the photos over the columns shortest-first, using the real aspect
 * ratio the API gives us. Heights are in units of column width, so the pixel
 * width of a column never matters. Every column starts empty, so the first
 * `columnCount` photos land one per column and the top row reads left-to-right.
 */
function distribute(photos: PhotoRead[], columnCount: number): PhotoRead[][] {
  const columns: PhotoRead[][] = Array.from({ length: columnCount }, () => [])
  const heights = new Array<number>(columnCount).fill(0)

  for (const photo of photos) {
    const ratio =
      photo.width && photo.height ? photo.height / photo.width : FALLBACK_RATIO
    const target = heights.indexOf(Math.min(...heights))
    columns[target].push(photo)
    heights[target] += ratio
  }

  return columns
}

/**
 * A masonry built from real flex columns, not CSS `columns-*`: multi-column
 * balances every column to the same height, so a handful of photos fills only
 * the first few columns and leaves the rest empty (6 photos over 4 columns
 * rendered as 2+2+2). Race photos mix portraits and landscapes, so the tiles
 * keep their aspect ratio -- the old `aspect-square` cropped the runner out.
 */
export function PhotoGrid({
  photos,
  selected,
  onToggleSelect,
  highlightBib,
}: PhotoGridProps) {
  const columnCount = useColumnCount()
  const columns = useMemo(
    () => distribute(photos, columnCount),
    [photos, columnCount],
  )

  return (
    <div className="flex items-start gap-3">
      {columns.map((column, i) => (
        <div key={i} className="flex min-w-0 flex-1 flex-col gap-3">
          {column.map((photo) => (
            <PhotoCard
              key={photo.id}
              photo={photo}
              selected={selected.has(photo.id)}
              onToggleSelect={onToggleSelect}
              highlightBib={highlightBib}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

export function PhotoGridSkeleton({ count = 6 }: { count?: number }) {
  const columnCount = useColumnCount()

  // Round-robin: skeletons have no dimensions to balance by, and dealing them
  // out one per column keeps every column occupied.
  return (
    <div className="flex items-start gap-3">
      {Array.from({ length: columnCount }, (_, col) => (
        <div key={col} className="flex min-w-0 flex-1 flex-col gap-3">
          {Array.from({ length: count }, (_, i) => i)
            .filter((i) => i % columnCount === col)
            .map((i) => (
              <PhotoCardSkeleton key={i} tall={i % 3 === 1} />
            ))}
        </div>
      ))}
    </div>
  )
}
