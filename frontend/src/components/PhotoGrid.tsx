import type { PhotoRead } from '@/types/api'
import { PhotoCard } from '@/components/PhotoCard'

interface PhotoGridProps {
  photos: PhotoRead[]
  selectedIds: Set<string>
  onToggleSelect: (id: string) => void
}

export function PhotoGrid({ photos, selectedIds, onToggleSelect }: PhotoGridProps) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {photos.map((photo) => (
        <PhotoCard
          key={photo.id}
          photo={photo}
          selected={selectedIds.has(photo.id)}
          onToggleSelect={onToggleSelect}
        />
      ))}
    </div>
  )
}
