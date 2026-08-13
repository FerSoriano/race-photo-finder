import { useState } from 'react'
import { UploadCloud, X } from 'lucide-react'
import { COVER_MIME_TYPES, MAX_COVER_BYTES } from '@/api/client'
import { EventCover } from '@/components/EventCover'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface CoverUploaderProps {
  slug: string
  coverUrl: string | null
  onUpload: (file: File) => void
  onRemove: () => void
  isUploading: boolean
  isRemoving: boolean
  error: string | null
}

/**
 * No drag-and-drop library -- a single-image drop is native drag events plus
 * a hidden file input, which is what this needs. Client-side checks mirror
 * services/cover.py's limits as an early hint; the server's 422 stays the
 * source of truth.
 */
export function CoverUploader({
  slug,
  coverUrl,
  onUpload,
  onRemove,
  isUploading,
  isRemoving,
  error,
}: CoverUploaderProps) {
  const [dragging, setDragging] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)
  const busy = isUploading || isRemoving

  const validateAndUpload = (file: File | undefined) => {
    if (!file) return
    setLocalError(null)
    if (!COVER_MIME_TYPES.includes(file.type)) {
      setLocalError('Solo se aceptan imágenes JPG, PNG o WebP.')
      return
    }
    if (file.size > MAX_COVER_BYTES) {
      setLocalError(
        `La imagen pesa ${(file.size / 1024 / 1024).toFixed(1)} MB, el límite es 5 MB.`,
      )
      return
    }
    onUpload(file)
  }

  return (
    <div className="flex flex-col gap-3">
      <div
        onDragOver={(event) => {
          event.preventDefault()
          if (!busy) setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragging(false)
          if (!busy) validateAndUpload(event.dataTransfer.files[0])
        }}
        className={cn(
          'relative aspect-21/9 overflow-hidden rounded-xl border-2 border-dashed transition-colors',
          dragging ? 'border-primary' : 'border-border',
        )}
      >
        <EventCover slug={slug} coverUrl={coverUrl} className="absolute inset-0 size-full" />

        <label
          className={cn(
            'absolute inset-0 flex cursor-pointer flex-col items-center justify-center gap-2 bg-background/50 text-center opacity-80 backdrop-blur-[1px] transition-opacity hover:opacity-100',
            dragging && 'bg-background/70 opacity-100',
            busy && 'pointer-events-none opacity-100',
          )}
        >
          <UploadCloud className="size-6" />
          <span className="text-sm font-medium">
            {isUploading ? 'Subiendo…' : 'Arrastra una imagen aquí o haz clic'}
          </span>
          <input
            type="file"
            accept={COVER_MIME_TYPES.join(',')}
            className="sr-only"
            disabled={busy}
            onChange={(event) => validateAndUpload(event.target.files?.[0])}
          />
        </label>
      </div>

      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">JPG, PNG o WebP -- máximo 5 MB.</p>
        {coverUrl && (
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground"
            disabled={busy}
            onClick={onRemove}
          >
            <X className="size-3.5" />
            {isRemoving ? 'Quitando…' : 'Quitar portada'}
          </Button>
        )}
      </div>

      {(localError || error) && <p className="text-sm text-destructive">{localError ?? error}</p>}
    </div>
  )
}
