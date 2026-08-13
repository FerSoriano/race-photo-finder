import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import type { EventCreatePayload } from '@/types/api'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { EventFormFields, emptyEventFormValues, type EventFormValues } from './EventFormFields'

// Matches EventCreate.slug's pattern in backend/src/rpf/schemas/events.py.
const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/

const COMBINING_MARKS = /[\u0300-\u036f]/g

function slugify(input: string): string {
  return input
    .normalize('NFD')
    .replace(COMBINING_MARKS, '') // strips accents left behind by NFD
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

interface EventCreateDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (payload: EventCreatePayload) => void
  isPending: boolean
  error: string | null
}

/** The slug auto-derives from the name until the operator edits it directly --
 * after that, typing the name no longer overwrites what they typed. */
export function EventCreateDialog({
  open,
  onOpenChange,
  onSubmit,
  isPending,
  error,
}: EventCreateDialogProps) {
  const [values, setValues] = useState<EventFormValues>(emptyEventFormValues)
  const [slug, setSlug] = useState('')
  const [slugTouched, setSlugTouched] = useState(false)

  useEffect(() => {
    if (open) {
      setValues(emptyEventFormValues)
      setSlug('')
      setSlugTouched(false)
    }
  }, [open])

  const handleFieldsChange = (next: EventFormValues) => {
    setValues(next)
    if (!slugTouched) setSlug(slugify(next.name))
  }

  const slugValid = SLUG_PATTERN.test(slug)
  const canSubmit = slugValid && values.name.trim().length > 0

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!canSubmit) return
    onSubmit({
      slug,
      name: values.name.trim(),
      event_date: values.event_date || null,
      location: values.location.trim() || null,
      description: values.description.trim() || null,
      is_published: false,
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger render={<Button className="font-heading font-bold" />}>
        <Plus className="size-4" />
        Nueva carrera
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Nueva carrera</DialogTitle>
            <DialogDescription>
              Se crea como borrador. Publícala cuando las fotos estén listas.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 flex flex-col gap-4">
            <EventFormFields
              idPrefix="create"
              values={values}
              onChange={handleFieldsChange}
              disabled={isPending}
            />

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="create-slug">Slug</Label>
              <Input
                id="create-slug"
                className="font-mono"
                value={slug}
                disabled={isPending}
                aria-invalid={slug.length > 0 && !slugValid}
                onChange={(event) => {
                  setSlugTouched(true)
                  setSlug(event.target.value)
                }}
              />
              <p className="text-xs text-muted-foreground">
                Parte de la URL pública. Solo minúsculas, números y guiones -- no se puede
                cambiar después.
              </p>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>

          <DialogFooter>
            <Button type="submit" disabled={!canSubmit || isPending}>
              {isPending ? 'Creando…' : 'Crear carrera'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
