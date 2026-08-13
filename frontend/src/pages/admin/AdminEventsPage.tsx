import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { createEvent, deleteEvent, listAdminEvents, updateEvent } from '@/api/client'
import { adminKeys } from '@/lib/adminQueries'
import type { EventCreatePayload } from '@/types/api'
import { AdminEventsTable } from '@/components/admin/AdminEventsTable'
import { EventCreateDialog } from '@/components/admin/EventCreateDialog'
import { EmptyBib } from '@/components/EmptyBib'
import { Skeleton } from '@/components/ui/skeleton'

export function AdminEventsPage() {
  const queryClient = useQueryClient()
  const [createOpen, setCreateOpen] = useState(false)
  const [pendingPublishSlug, setPendingPublishSlug] = useState<string | null>(null)
  const [pendingDeleteSlug, setPendingDeleteSlug] = useState<string | null>(null)

  const eventsQuery = useQuery({
    queryKey: adminKeys.events,
    queryFn: listAdminEvents,
    retry: false,
  })

  // Publishing changes what the public routes return, so the public list
  // must be invalidated too -- it's one SPA and one QueryClient.
  const invalidateAfterWrite = () => {
    queryClient.invalidateQueries({ queryKey: adminKeys.events })
    queryClient.invalidateQueries({ queryKey: adminKeys.stats })
    queryClient.invalidateQueries({ queryKey: ['events'] })
  }

  const createMutation = useMutation({
    mutationFn: (payload: EventCreatePayload) => createEvent(payload),
    onSuccess: () => {
      invalidateAfterWrite()
      setCreateOpen(false)
      toast.success('Carrera creada como borrador')
    },
  })

  const publishMutation = useMutation({
    mutationFn: ({ slug, is_published }: { slug: string; is_published: boolean }) =>
      updateEvent(slug, { is_published }),
    onMutate: ({ slug }) => setPendingPublishSlug(slug),
    onSettled: () => setPendingPublishSlug(null),
    onSuccess: (_data, { is_published }) => {
      invalidateAfterWrite()
      toast.success(is_published ? 'Carrera publicada' : 'Carrera despublicada')
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : 'No se pudo actualizar la carrera')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (slug: string) => deleteEvent(slug),
    onMutate: (slug) => setPendingDeleteSlug(slug),
    onSettled: () => setPendingDeleteSlug(null),
    onSuccess: () => {
      invalidateAfterWrite()
      toast.success('Carrera eliminada')
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : 'No se pudo eliminar la carrera')
    },
  })

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-bold tracking-tight">Carreras</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Publicadas y borradores -- todo lo que existe en el catálogo.
          </p>
        </div>
        <EventCreateDialog
          open={createOpen}
          onOpenChange={setCreateOpen}
          onSubmit={(payload) => createMutation.mutate(payload)}
          isPending={createMutation.isPending}
          error={createMutation.isError ? (createMutation.error as Error).message : null}
        />
      </div>

      <div className="mt-6 overflow-hidden rounded-xl border border-border">
        {eventsQuery.isLoading && (
          <div className="flex flex-col gap-2 p-4">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {eventsQuery.isError && (
          <div className="flex flex-col items-center py-12 text-center">
            <EmptyBib label="!" />
            <h2 className="mt-6 font-heading text-lg font-bold">
              No pudimos cargar las carreras
            </h2>
          </div>
        )}

        {eventsQuery.data && eventsQuery.data.length === 0 && (
          <div className="flex flex-col items-center py-12 text-center">
            <EmptyBib />
            <h2 className="mt-6 font-heading text-lg font-bold">Todavía no hay carreras</h2>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Crea la primera con el botón de arriba.
            </p>
          </div>
        )}

        {eventsQuery.data && eventsQuery.data.length > 0 && (
          <AdminEventsTable
            events={eventsQuery.data}
            onTogglePublish={(event, next) =>
              publishMutation.mutate({ slug: event.slug, is_published: next })
            }
            pendingPublishSlug={pendingPublishSlug}
            onDelete={(slug) => deleteMutation.mutate(slug)}
            pendingDeleteSlug={pendingDeleteSlug}
          />
        )}
      </div>
    </div>
  )
}
