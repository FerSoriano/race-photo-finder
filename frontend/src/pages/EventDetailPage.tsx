import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { getEvent, MAX_BULK_DOWNLOAD, requestBulkDownload, searchPhotos } from '@/api/client'
import { triggerDownloads } from '@/lib/download'
import { SearchBox } from '@/components/SearchBox'
import { PhotoGrid } from '@/components/PhotoGrid'
import { PossibleMatches } from '@/components/PossibleMatches'
import { SelectionBar } from '@/components/SelectionBar'

function formatDate(iso: string | null) {
  if (!iso) return null
  return new Date(iso).toLocaleDateString('es-MX', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

export function EventDetailPage() {
  const { slug = '' } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const bib = searchParams.get('bib') ?? ''
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

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
      setSelectedIds(new Set())
    },
  })

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const promoteBib = (newBib: string) => {
    setSearchParams({ bib: newBib })
  }

  const hasExactMatches = (searchQuery.data?.photos.length ?? 0) > 0
  const hasSimilar = (searchQuery.data?.similar_bibs.length ?? 0) > 0
  const noMatchesAtAll = Boolean(searchQuery.data) && !hasExactMatches && !hasSimilar

  return (
    <main className="mx-auto max-w-2xl px-4 py-8 pb-28 sm:py-12">
      <header className="mb-8">
        {eventQuery.data && (
          <>
            <h1 className="text-2xl font-heading font-semibold text-foreground sm:text-3xl">
              {eventQuery.data.name}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {[formatDate(eventQuery.data.event_date), eventQuery.data.location]
                .filter(Boolean)
                .join(' · ')}
            </p>
          </>
        )}
        {eventQuery.isError && (
          <p className="text-destructive">No encontramos esta carrera.</p>
        )}
      </header>

      <SearchBox defaultValue={bib} onSearch={promoteBib} />

      <div className="mt-8">
        {searchQuery.isLoading && (
          <p className="text-center text-muted-foreground">Buscando tus fotos…</p>
        )}

        {searchQuery.isError && (
          <p className="text-center text-destructive">
            No pudimos buscar tus fotos. Intenta de nuevo.
          </p>
        )}

        {hasExactMatches && searchQuery.data && (
          <section>
            <h2 className="text-lg font-heading font-semibold text-foreground">
              Tus fotos
            </h2>
            <div className="mt-4">
              <PhotoGrid
                photos={searchQuery.data.photos}
                selectedIds={selectedIds}
                onToggleSelect={toggleSelect}
              />
            </div>
          </section>
        )}

        {hasSimilar && searchQuery.data && (
          <PossibleMatches
            eventSlug={slug}
            bibs={searchQuery.data.similar_bibs}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onPromote={promoteBib}
          />
        )}

        {noMatchesAtAll && (
          <p className="text-center text-muted-foreground">
            No encontramos fotos con el número {bib}.
          </p>
        )}
      </div>

      <SelectionBar
        count={selectedIds.size}
        maxAllowed={MAX_BULK_DOWNLOAD}
        isDownloading={downloadMutation.isPending}
        error={downloadMutation.isError ? (downloadMutation.error as Error).message : null}
        onDownload={() => downloadMutation.mutate(Array.from(selectedIds))}
      />
    </main>
  )
}
