import { Button } from '@/components/ui/button'

interface SelectionBarProps {
  count: number
  maxAllowed: number
  isDownloading: boolean
  error: string | null
  onDownload: () => void
}

export function SelectionBar({
  count,
  maxAllowed,
  isDownloading,
  error,
  onDownload,
}: SelectionBarProps) {
  if (count === 0) return null

  const overLimit = count > maxAllowed

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-2xl flex-col gap-2 px-4 py-3">
        {overLimit && (
          <p className="text-xs text-destructive">
            Selecciona como máximo {maxAllowed} fotos por descarga.
          </p>
        )}
        {error && <p className="text-xs text-destructive">{error}</p>}
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm font-medium">
            {count} {count === 1 ? 'foto seleccionada' : 'fotos seleccionadas'}
          </span>
          <Button
            size="lg"
            className="px-6 text-base"
            onClick={onDownload}
            disabled={isDownloading || overLimit}
          >
            {isDownloading ? 'Preparando…' : 'Descargar seleccionadas'}
          </Button>
        </div>
      </div>
    </div>
  )
}
