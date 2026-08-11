import { useQueries } from '@tanstack/react-query'
import { searchPhotos } from '@/api/client'
import { PhotoGrid } from '@/components/PhotoGrid'

interface PossibleMatchesProps {
  eventSlug: string
  bibs: string[]
  selectedIds: Set<string>
  onToggleSelect: (id: string) => void
  onPromote: (bib: string) => void
}

// `similar_bibs` from the API is just a list of near-miss bib numbers, not
// photos -- fan out one search per suggestion so the runner sees actual
// thumbnails ("¿Eres tú?") instead of a bare list of numbers to tap through.
export function PossibleMatches({
  eventSlug,
  bibs,
  selectedIds,
  onToggleSelect,
  onPromote,
}: PossibleMatchesProps) {
  const results = useQueries({
    queries: bibs.map((bib) => ({
      queryKey: ['photos', eventSlug, bib],
      queryFn: () => searchPhotos(eventSlug, bib),
    })),
  })

  const rows = bibs
    .map((bib, i) => ({ bib, query: results[i] }))
    .filter((row) => (row.query.data?.photos.length ?? 0) > 0)

  const stillLoading = results.some((r) => r.isLoading)

  if (rows.length === 0 && !stillLoading) return null

  return (
    <section className="mt-8">
      <h2 className="text-lg font-heading font-semibold text-foreground">
        ¿Eres tú?
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        No encontramos ese número exacto, pero estas fotos tienen números
        parecidos.
      </p>

      {rows.length === 0 && stillLoading && (
        <p className="mt-4 text-sm text-muted-foreground">Buscando…</p>
      )}

      <div className="mt-4 flex flex-col gap-6">
        {rows.map(({ bib, query }) => (
          <div key={bib}>
            <button
              type="button"
              onClick={() => onPromote(bib)}
              className="mb-2 text-sm font-medium text-primary hover:underline"
            >
              ¿Buscabas el número {bib}?
            </button>
            <PhotoGrid
              photos={query.data!.photos}
              selectedIds={selectedIds}
              onToggleSelect={onToggleSelect}
            />
          </div>
        ))}
      </div>
    </section>
  )
}
