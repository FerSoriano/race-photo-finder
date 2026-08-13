import { useState, type ReactElement } from 'react'
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
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface DeleteEventDialogProps {
  slug: string
  name: string
  trigger: ReactElement
  onConfirm: () => void
  isPending: boolean
}

/**
 * Deletion cascades to every photo and the cover, in the database and in
 * object storage, and cannot be undone -- typing the slug is the confirmation,
 * matching the weight of the action (the existing "Quitar todo" alert-dialog
 * only discards a selection, which is a weaker precedent).
 */
export function DeleteEventDialog({ slug, name, trigger, onConfirm, isPending }: DeleteEventDialogProps) {
  const [open, setOpen] = useState(false)
  const [confirmText, setConfirmText] = useState('')
  const canConfirm = confirmText.trim() === slug

  return (
    <AlertDialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (!next) setConfirmText('')
      }}
    >
      <AlertDialogTrigger render={trigger} />
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Eliminar "{name}"?</AlertDialogTitle>
          <AlertDialogDescription>
            Se borran también todas sus fotos y la portada, en la base de datos y en el
            almacenamiento. No se puede deshacer.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="flex flex-col gap-1.5 px-1">
          <Label htmlFor={`confirm-delete-${slug}`}>
            Escribe <span className="font-mono text-foreground">{slug}</span> para confirmar
          </Label>
          <Input
            id={`confirm-delete-${slug}`}
            value={confirmText}
            autoComplete="off"
            autoFocus
            onChange={(event) => setConfirmText(event.target.value)}
          />
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            disabled={!canConfirm || isPending}
            onClick={onConfirm}
          >
            {isPending ? 'Eliminando…' : 'Eliminar'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
