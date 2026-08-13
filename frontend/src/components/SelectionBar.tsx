import { useState } from 'react'
import { X } from 'lucide-react'
import type { PhotoRead } from '@/types/api'
import { Button } from '@/components/ui/button'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'

interface SelectionBarProps {
  photos: PhotoRead[]
  maxAllowed: number
  isDownloading: boolean
  error: string | null
  onDownload: () => void
  onRemove: (id: string) => void
  onClear: () => void
}

export function SelectionBar({
  photos,
  maxAllowed,
  isDownloading,
  error,
  onDownload,
  onRemove,
  onClear,
}: SelectionBarProps) {
  const [confirmOpen, setConfirmOpen] = useState(false)

  const count = photos.length
  if (count === 0) return null

  const overLimit = count > maxAllowed
  // Warn on the last slot rather than only after the server would reject.
  const nearLimit = !overLimit && count >= maxAllowed - 1

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-card/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-3">
        {/* Which photos, not just how many. */}
        <ul className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
          {photos.map((photo) => (
            <li key={photo.id} className="relative flex-none">
              <img
                src={photo.thumb_url}
                alt=""
                className="size-14 rounded-md object-cover"
              />
              <button
                type="button"
                onClick={() => onRemove(photo.id)}
                aria-label="Quitar esta foto de la selección"
                className="absolute -top-1 -right-1 grid size-5 place-items-center rounded-full bg-background/90 text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              >
                <X className="size-3" />
              </button>
            </li>
          ))}
        </ul>

        {overLimit && (
          <p className="text-xs text-warning">
            Puedes descargar hasta {maxAllowed} fotos a la vez. Quita{' '}
            {count - maxAllowed} para continuar.
          </p>
        )}
        {nearLimit && (
          <p className="text-xs text-warning">
            Te queda {maxAllowed - count === 1 ? '1 espacio' : 'poco espacio'} en
            esta descarga.
          </p>
        )}
        {error && <p className="text-xs text-destructive">{error}</p>}

        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span
              className={`font-heading text-lg font-extrabold tabular-nums ${
                overLimit || nearLimit ? 'text-warning' : 'text-foreground'
              }`}
            >
              {count}
              <span className="text-muted-foreground"> / {maxAllowed}</span>
            </span>

            <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
              <AlertDialogTrigger
                render={
                  <Button variant="ghost" size="sm" className="text-muted-foreground" />
                }
              >
                Quitar todo
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>¿Quitar las {count} fotos?</AlertDialogTitle>
                  <AlertDialogDescription>
                    Vas a empezar tu selección de cero. Tus fotos siguen aquí,
                    solo se deseleccionan.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancelar</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => {
                      onClear()
                      setConfirmOpen(false)
                    }}
                  >
                    Quitar todo
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>

          <Button
            size="lg"
            className="font-heading font-bold"
            onClick={onDownload}
            disabled={isDownloading || overLimit}
          >
            {isDownloading ? 'Preparando…' : 'Descargar'}
          </Button>
        </div>
      </div>
    </div>
  )
}
