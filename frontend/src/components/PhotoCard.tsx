import type { PhotoRead } from '@/types/api'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

interface PhotoCardProps {
  photo: PhotoRead
  selected: boolean
  onToggleSelect: (id: string) => void
}

export function PhotoCard({ photo, selected, onToggleSelect }: PhotoCardProps) {
  const bibsLabel = photo.bibs.map((b) => b.number).join(', ')

  return (
    <Dialog>
      <div className="group relative aspect-square overflow-hidden rounded-lg bg-muted">
        <label
          className="absolute top-2 left-2 z-10 flex size-7 items-center justify-center rounded-md bg-background/90 shadow-sm"
          onClick={(e) => e.stopPropagation()}
        >
          <Checkbox
            checked={selected}
            onCheckedChange={() => onToggleSelect(photo.id)}
            aria-label="Seleccionar foto"
          />
        </label>
        <DialogTrigger className="block h-full w-full">
          <img
            src={photo.thumb_url}
            alt={bibsLabel ? `Foto con número ${bibsLabel}` : 'Foto de carrera'}
            loading="lazy"
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
          />
        </DialogTrigger>
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
