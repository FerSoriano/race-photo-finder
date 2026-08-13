import type { PhotoRead } from '@/types/api'
import { PhotoCard, PhotoCardSkeleton } from '@/components/PhotoCard'

interface PhotoGridProps {
  photos: PhotoRead[]
  selected: ReadonlyMap<string, PhotoRead>
  onToggleSelect: (photo: PhotoRead) => void
  highlightBib?: string
}

/**
 * CSS columns rather than a fixed grid: race photos are a mix of portraits and
 * landscapes, and the old `aspect-square` cropped the runner out of both.
 * Columns fill top-to-bottom instead of left-to-right, which is fine here --
 * the photos carry no meaningful order.
 */
export function PhotoGrid({
  photos,
  selected,
  onToggleSelect,
  highlightBib,
}: PhotoGridProps) {
  return (
    <div className="columns-2 gap-3 sm:columns-3 lg:columns-4">
      {photos.map((photo) => (
        <PhotoCard
          key={photo.id}
          photo={photo}
          selected={selected.has(photo.id)}
          onToggleSelect={onToggleSelect}
          highlightBib={highlightBib}
        />
      ))}
    </div>
  )
}

export function PhotoGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="columns-2 gap-3 sm:columns-3 lg:columns-4">
      {Array.from({ length: count }, (_, i) => (
        <PhotoCardSkeleton key={i} tall={i % 3 === 1} />
      ))}
    </div>
  )
}
