import { useQuery } from '@tanstack/react-query'
import { getEvents } from '@/api/client'
import { EventCard, EventCardSkeleton } from '@/components/EventCard'
import { EmptyBib } from '@/components/EmptyBib'

export function EventsListPage() {
  const { data: events, isLoading, isError } = useQuery({
    queryKey: ['events'],
    queryFn: getEvents,
  })

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:py-12">
      <header className="max-w-2xl">
        <h1 className="font-heading text-[2.25rem] leading-[1.05] font-extrabold tracking-[-0.03em] text-balance sm:text-5xl">
          Encuentra tus fotos de carrera
        </h1>
        <p className="mt-3 text-muted-foreground">
          Elige tu carrera y busca con tu número de corredor.
        </p>
      </header>

      <div className="mt-8">
        {isLoading && (
          <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <li key={i}>
                <EventCardSkeleton />
              </li>
            ))}
          </ul>
        )}

        {isError && (
          <div className="flex flex-col items-center py-12 text-center">
            <EmptyBib label="!" />
            <h2 className="mt-6 font-heading text-lg font-bold">
              No pudimos cargar las carreras
            </h2>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Revisa tu conexión y vuelve a intentar en un momento.
            </p>
          </div>
        )}

        {events && events.length === 0 && (
          <div className="flex flex-col items-center py-12 text-center">
            <EmptyBib />
            <h2 className="mt-6 font-heading text-lg font-bold">
              Aún no hay carreras publicadas
            </h2>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              En cuanto subamos las fotos de la próxima carrera, van a aparecer
              aquí.
            </p>
          </div>
        )}

        {events && events.length > 0 && (
          <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {events.map((event) => (
              <li key={event.id}>
                <EventCard event={event} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  )
}
