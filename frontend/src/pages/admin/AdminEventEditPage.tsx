import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { ExternalLink, Trash2 } from 'lucide-react'
import {
  deleteCover,
  deleteEvent,
  getAdminEvent,
  updateEvent,
  uploadCover,
} from '@/api/client'
import { adminKeys } from '@/lib/adminQueries'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyBib } from '@/components/EmptyBib'
import { CoverUploader } from '@/components/admin/CoverUploader'
import { DeleteEventDialog } from '@/components/admin/DeleteEventDialog'
import { EventFormFields, emptyEventFormValues, type EventFormValues } from '@/components/admin/EventFormFields'

export function AdminEventEditPage() {
  const { slug = '' } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [values, setValues] = useState<EventFormValues>(emptyEventFormValues)

  const eventQuery = useQuery({
    queryKey: adminKeys.event(slug),
    queryFn: () => getAdminEvent(slug),
    retry: false,
  })

  // Seed the form once the row loads. Re-seeds if the slug in the URL
  // changes (navigating between two edit pages reuses the component).
  useEffect(() => {
    if (eventQuery.data) {
      setValues({
        name: eventQuery.data.name,
        event_date: eventQuery.data.event_date ?? '',
        location: eventQuery.data.location ?? '',
        description: eventQuery.data.description ?? '',
      })
    }
  }, [eventQuery.data])

  const invalidateAfterWrite = () => {
    queryClient.invalidateQueries({ queryKey: adminKeys.event(slug) })
    queryClient.invalidateQueries({ queryKey: adminKeys.events })
    queryClient.invalidateQueries({ queryKey: adminKeys.stats })
    queryClient.invalidateQueries({ queryKey: ['events'] })
    queryClient.invalidateQueries({ queryKey: ['event', slug] })
  }

  const updateMutation = useMutation({
    mutationFn: (payload: EventFormValues) =>
      updateEvent(slug, {
        name: payload.name.trim(),
        event_date: payload.event_date || null,
        location: payload.location.trim() || null,
        description: payload.description.trim() || null,
      }),
    onSuccess: () => {
      invalidateAfterWrite()
      toast.success('Cambios guardados')
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : 'No se pudo guardar')
    },
  })

  const uploadCoverMutation = useMutation({
    mutationFn: (file: File) => uploadCover(slug, file),
    onSuccess: () => {
      invalidateAfterWrite()
      toast.success('Portada actualizada')
    },
  })

  const deleteCoverMutation = useMutation({
    mutationFn: () => deleteCover(slug),
    onSuccess: () => {
      invalidateAfterWrite()
      toast.success('Portada eliminada')
    },
  })

  const deleteEventMutation = useMutation({
    mutationFn: () => deleteEvent(slug),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: adminKeys.event(slug) })
      queryClient.removeQueries({ queryKey: ['event', slug] })
      queryClient.invalidateQueries({ queryKey: adminKeys.events })
      queryClient.invalidateQueries({ queryKey: adminKeys.stats })
      queryClient.invalidateQueries({ queryKey: ['events'] })
      toast.success('Carrera eliminada')
      navigate('/admin/eventos')
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : 'No se pudo eliminar la carrera')
    },
  })

  if (eventQuery.isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  if (eventQuery.isError || !eventQuery.data) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <EmptyBib label="?" />
        <h1 className="mt-6 font-heading text-lg font-bold">No encontramos esta carrera</h1>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          Puede que el slug esté mal escrito o que la carrera se haya eliminado.
        </p>
        <Button className="mt-6" nativeButton={false} render={<Link to="/admin/eventos" />}>
          Volver a carreras
        </Button>
      </div>
    )
  }

  const event = eventQuery.data

  const handleSubmit = (formEvent: React.FormEvent) => {
    formEvent.preventDefault()
    if (!values.name.trim()) return
    updateMutation.mutate(values)
  }

  return (
    <div className="flex max-w-2xl flex-col gap-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-bold tracking-tight">{event.name}</h1>
          <p className="mt-1 font-mono text-sm text-muted-foreground">
            {event.slug} · {event.photo_count} fotos
          </p>
        </div>
        {event.is_published && (
          <Button
            variant="outline"
            size="sm"
            nativeButton={false}
            render={<Link to={`/eventos/${event.slug}`} />}
          >
            <ExternalLink className="size-3.5" />
            Ver en el sitio
          </Button>
        )}
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="font-heading text-sm font-semibold tracking-wide text-muted-foreground uppercase">
          Portada
        </h2>
        <CoverUploader
          slug={event.slug}
          coverUrl={event.cover_url}
          onUpload={(file) => uploadCoverMutation.mutate(file)}
          onRemove={() => deleteCoverMutation.mutate()}
          isUploading={uploadCoverMutation.isPending}
          isRemoving={deleteCoverMutation.isPending}
          error={
            uploadCoverMutation.isError
              ? (uploadCoverMutation.error as Error).message
              : deleteCoverMutation.isError
                ? (deleteCoverMutation.error as Error).message
                : null
          }
        />
      </section>

      <section>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <h2 className="font-heading text-sm font-semibold tracking-wide text-muted-foreground uppercase">
            Detalles
          </h2>

          <div className="flex flex-col gap-1.5">
            <span className="text-sm leading-none font-medium">Slug</span>
            <p className="font-mono text-sm text-muted-foreground">{event.slug}</p>
            <p className="text-xs text-muted-foreground">
              No se puede cambiar -- rompería los enlaces ya compartidos.
            </p>
          </div>

          <EventFormFields
            idPrefix="edit"
            values={values}
            onChange={setValues}
            disabled={updateMutation.isPending}
          />

          <div>
            <Button
              type="submit"
              className="font-heading font-bold"
              disabled={updateMutation.isPending || !values.name.trim()}
            >
              {updateMutation.isPending ? 'Guardando…' : 'Guardar cambios'}
            </Button>
          </div>
        </form>
      </section>

      <section className="flex flex-col gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4">
        <h2 className="font-heading text-sm font-semibold tracking-wide text-destructive uppercase">
          Zona peligrosa
        </h2>
        <p className="text-sm text-muted-foreground">
          Elimina esta carrera junto con todas sus fotos y la portada. No se puede deshacer.
        </p>
        <div>
          <DeleteEventDialog
            slug={event.slug}
            name={event.name}
            isPending={deleteEventMutation.isPending}
            onConfirm={() => deleteEventMutation.mutate()}
            trigger={
              <Button variant="destructive" size="sm">
                <Trash2 className="size-3.5" />
                Eliminar carrera
              </Button>
            }
          />
        </div>
      </section>
    </div>
  )
}
