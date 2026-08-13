import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import type { PhotoRead } from '@/types/api'
import { getEvent, MAX_BULK_DOWNLOAD, requestBulkDownload, searchPhotos } from '@/api/client'
import { triggerDownloads } from '@/lib/download'
import { formatEventMeta } from '@/lib/format'
import { Bib } from '@/components/Bib'
import { EventCover } from '@/components/EventCover'
import { PhotoGrid, PhotoGridSkeleton } from '@/components/PhotoGrid'
import { PossibleMatches } from '@/components/PossibleMatches'
import { SelectionBar } from '@/components/SelectionBar'
import { EmptyBib } from '@/components/EmptyBib'
import { Skeleton } from '@/components/ui/skeleton'

export function EventDetailPage() {
  const { slug = '' } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const bib = searchParams.get('bib') ?? ''

  // Keyed by photo id, holding the whole photo: the selection bar shows
  // thumbnails, and a selected photo may come from a "¿Eres tú?" section whose
  // data this page never fetched.
  const [selected, setSelected] = useState<Map<string, PhotoRead>>(new Map())

  const eventQuery = useQuery({
    queryKey: ['event', slug],
    queryFn: () => getEvent(slug),
  })

  const searchQuery = useQuery({
    queryKey: ['photos', slug, bib],
    queryFn: () => searchPhotos(slug, bib),
    enabled: bib.length > 0,
  })

  const downloadMutation = useMutation({
    mutationFn: (ids: string[]) => requestBulkDownload(slug, ids),
    onSuccess: (result) => {
      triggerDownloads(result.photos)
      setSelected(new Map())
      toast.success(
        result.photos.length === 1
          ? 'Descargando tu foto'
          : `Descargando tus ${result.photos.length} fotos`,
        { description: 'Búscalas en las descargas de tu teléfono.' },
      )
    },
  })

  const toggleSelect = (photo: PhotoRead) => {
    setSelected((prev) => {
      const next = new Map(prev)
      if (next.has(photo.id)) next.delete(photo.id)
      else next.set(photo.id, photo)
      return next
    })
  }

  const removeSelected = (id: string) => {
    setSelected((prev) => {
      const next = new Map(prev)
      next.delete(id)
      return next
    })
  }

  const promoteBib = (newBib: string) => {
    setSearchParams({ bib: newBib })
  }

  const event = eventQuery.data
  const hasExactMatches = (searchQuery.data?.photos.length ?? 0) > 0
  const hasSimilar = (searchQuery.data?.similar_bibs.length ?? 0) > 0
  const noMatchesAtAll = Boolean(searchQuery.data) && !hasExactMatches && !hasSimilar

  if (eventQuery.isError) {
    return (
      <main className="mx-auto flex max-w-md flex-col items-center px-4 py-16 text-center sm:py-24">
        <EmptyBib label="?" />
        <h1 className="mt-8 font-heading text-2xl font-bold tracking-tight">
          No encontramos esta carrera
        </h1>
        <p className="mt-2 text-muted-foreground">
          Puede que el enlace haya cambiado. Revisa la lista de carreras
          publicadas.
        </p>
      </main>
    )
  }

  return (
    <main className="pb-40">
      {/* The hero: the bib search is the whole product, so it opens the page
          instead of sitting two thirds down it. */}
      <section className="relative">
        <EventCover
          slug={slug}
          coverUrl={event?.cover_url ?? null}
          className="absolute inset-0 h-full"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/70 via-background/85 to-background" />

        <div className="relative mx-auto max-w-md px-4 pt-8 pb-10 sm:pt-12">
          <header className="mb-7 text-center">
            {event ? (
              <>
                <h1 className="font-heading text-[1.75rem] leading-tight font-bold tracking-tight text-balance sm:text-4xl">
                  {event.name}
                </h1>
                <p className="mt-2 text-sm tabular-nums text-muted-foreground">
                  {[
                    formatEventMeta(event.event_date, event.location),
                    `${event.photo_count} fotos`,
                  ]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
              </>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <Skeleton className="h-8 w-64" />
                <Skeleton className="h-4 w-44" />
              </div>
            )}
          </header>

          <Bib
            eventName={event?.name ?? ''}
            defaultValue={bib}
            onSearch={promoteBib}
          />
        </div>
      </section>

      <div className="mx-auto max-w-5xl px-4">
        {searchQuery.isLoading && (
          <section>
            <SectionTitle>Buscando</SectionTitle>
            <div className="mt-4">
              <PhotoGridSkeleton />
            </div>
          </section>
        )}

        {searchQuery.isError && (
          <div className="flex flex-col items-center py-10 text-center">
            <EmptyBib label="!" />
            <h2 className="mt-6 font-heading text-lg font-bold">
              No pudimos buscar tus fotos
            </h2>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Revisa tu conexión y vuelve a intentar.
            </p>
          </div>
        )}

        {hasExactMatches && searchQuery.data && (
          <section>
            <SectionTitle>Tus fotos · {searchQuery.data.photos.length}</SectionTitle>
            <div className="mt-4">
              <PhotoGrid
                photos={searchQuery.data.photos}
                selected={selected}
                onToggleSelect={toggleSelect}
                highlightBib={bib}
              />
            </div>
          </section>
        )}

        {hasSimilar && searchQuery.data && (
          <PossibleMatches
            eventSlug={slug}
            bibs={searchQuery.data.similar_bibs}
            selected={selected}
            onToggleSelect={toggleSelect}
            onPromote={promoteBib}
          />
        )}

        {noMatchesAtAll && (
          <div className="flex flex-col items-center py-10 text-center">
            <EmptyBib label={bib.slice(0, 5)} />
            <h2 className="mt-6 font-heading text-lg font-bold">
              No encontramos fotos con el {bib}
            </h2>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Revisa que el número sea el mismo que traías puesto. Si traías el
              dorsal doblado o tapado, puede que no se haya alcanzado a leer.
            </p>
          </div>
        )}
      </div>

      <SelectionBar
        photos={Array.from(selected.values())}
        maxAllowed={MAX_BULK_DOWNLOAD}
        isDownloading={downloadMutation.isPending}
        error={downloadMutation.isError ? (downloadMutation.error as Error).message : null}
        onDownload={() => downloadMutation.mutate(Array.from(selected.keys()))}
        onRemove={removeSelected}
        onClear={() => setSelected(new Map())}
      />
    </main>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="font-heading text-xs font-semibold tracking-[0.1em] tabular-nums text-muted-foreground uppercase">
      {children}
    </h2>
  )
}
