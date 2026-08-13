import type { PhotoRead } from '@/types/api'
import { Checkbox } from '@/components/ui/checkbox'
import { BibBadge } from '@/components/BibBadge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

interface PhotoCardProps {
  photo: PhotoRead
  selected: boolean
  /** Passes the whole photo, not just its id, so the selection bar can show
      thumbnails for photos that came from a "¿Eres tú?" section too. */
  onToggleSelect: (photo: PhotoRead) => void
  /** The bib being searched, so the tile badges that one and not a stranger's. */
  highlightBib?: string
}

export function PhotoCard({
  photo,
  selected,
  onToggleSelect,
  highlightBib,
}: PhotoCardProps) {
  const bibsLabel = photo.bibs.map((b) => b.number).join(', ')
  const badge =
    photo.bibs.find((b) => b.number === highlightBib) ?? photo.bibs[0]

  // The API gives real dimensions -- handing them to the browser reserves the
  // right box before the image lands, so the masonry doesn't reflow.
  const hasSize = photo.width !== null && photo.height !== null

  return (
    <Dialog>
      <div
        className={`group relative mb-3 break-inside-avoid overflow-hidden rounded-lg bg-card ${
          selected ? 'ring-2 ring-primary ring-inset' : ''
        }`}
      >
        <DialogTrigger className="block w-full cursor-zoom-in">
          <img
            src={photo.thumb_url}
            alt={bibsLabel ? `Foto con número ${bibsLabel}` : 'Foto de carrera'}
            loading="lazy"
            decoding="async"
            {...(hasSize
              ? { width: photo.width!, height: photo.height! }
              : {})}
            className={
              hasSize
                ? 'block h-auto w-full'
                : 'block aspect-3/4 w-full object-cover'
            }
          />
        </DialogTrigger>

        {/* Big enough to hit with a thumb without opening the preview. */}
        <label
          className="absolute top-1.5 left-1.5 z-10 flex size-9 cursor-pointer items-center justify-center rounded-md bg-background/70 backdrop-blur-sm transition-colors has-[:checked]:bg-primary"
          onClick={(e) => e.stopPropagation()}
        >
          <Checkbox
            checked={selected}
            onCheckedChange={() => onToggleSelect(photo)}
            aria-label={
              selected
                ? `Quitar la foto ${bibsLabel} de la selección`
                : `Seleccionar la foto ${bibsLabel}`
            }
          />
        </label>

        {badge && (
          <BibBadge
            number={badge.number}
            uncertain={badge.is_uncertain}
            className="absolute right-1.5 bottom-1.5 z-10"
          />
        )}
      </div>

      <DialogContent className="sm:max-w-2xl">
        <DialogTitle className="sr-only">Vista previa de la foto</DialogTitle>
        <img
          src={photo.preview_url}
          alt={bibsLabel ? `Foto con número ${bibsLabel}` : 'Foto de carrera'}
          className="w-full rounded-lg"
        />
        <p className="text-xs text-muted-foreground">
          Vista previa con marca de agua. Selecciona la foto en la cuadrícula
          para descargar el original.
        </p>
      </DialogContent>
    </Dialog>
  )
}

/** Staggered heights so the loading state reads as a photo wall, not a table. */
export function PhotoCardSkeleton({ tall }: { tall?: boolean }) {
  return (
    <Skeleton
      className={`mb-3 w-full break-inside-avoid rounded-lg ${tall ? 'h-56' : 'h-40'}`}
    />
  )
}
