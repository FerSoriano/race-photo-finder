import { useQueries } from '@tanstack/react-query'
import type { PhotoRead } from '@/types/api'
import { searchPhotos } from '@/api/client'
import { PhotoGrid, PhotoGridSkeleton } from '@/components/PhotoGrid'
import { BibBadge } from '@/components/BibBadge'
import { Button } from '@/components/ui/button'

interface PossibleMatchesProps {
  eventSlug: string
  bibs: string[]
  selected: ReadonlyMap<string, PhotoRead>
  onToggleSelect: (photo: PhotoRead) => void
  onPromote: (bib: string) => void
}

// `similar_bibs` from the API is just a list of near-miss bib numbers, not
// photos -- fan out one search per suggestion so the runner sees actual
// thumbnails ("¿Eres tú?") instead of a bare list of numbers to tap through.
//
// This is the most product-specific screen in the app: when the detector
// misreads a digit, it is the only way the runner ever finds their photo. It
// is designed as a recovery path, not as an error -- hence amber, never red.
export function PossibleMatches({
  eventSlug,
  bibs,
  selected,
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
    <section className="mt-10">
      <h2 className="font-heading text-xs font-semibold tracking-[0.1em] text-warning uppercase">
        ¿Eres tú?
      </h2>
      <p className="mt-2 max-w-prose text-sm text-muted-foreground">
        No encontramos ese número exacto, pero estas fotos tienen números
        parecidos. A veces el número se lee mal por el sudor, un doblez o el
        ángulo de la foto.
      </p>

      {rows.length === 0 && stillLoading && (
        <div className="mt-5">
          <PhotoGridSkeleton count={4} />
        </div>
      )}

      <div className="mt-5 flex flex-col gap-4">
        {rows.map(({ bib, query }) => {
          const total = query.data!.photos.length

          return (
            <div
              key={bib}
              className="rounded-xl border border-warning/25 bg-warning/[0.04] p-3 sm:p-4"
            >
              <div className="mb-3 flex items-center gap-2">
                <BibBadge number={bib} />
                <span className="text-sm tabular-nums text-muted-foreground">
                  {total} {total === 1 ? 'foto' : 'fotos'}
                </span>
              </div>

              <PhotoGrid
                photos={query.data!.photos}
                selected={selected}
                onToggleSelect={onToggleSelect}
                highlightBib={bib}
              />

              <Button
                type="button"
                size="lg"
                onClick={() => onPromote(bib)}
                className="w-full border border-warning/40 bg-warning/10 font-heading font-bold text-warning hover:bg-warning/20"
              >
                Sí, soy el {bib}
              </Button>
            </div>
          )
        })}
      </div>
    </section>
  )
}
