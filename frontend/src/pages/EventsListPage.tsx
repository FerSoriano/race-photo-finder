import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getEvents } from '@/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

function formatDate(iso: string | null) {
  if (!iso) return null
  return new Date(iso).toLocaleDateString('es-MX', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

export function EventsListPage() {
  const { data: events, isLoading, isError } = useQuery({
    queryKey: ['events'],
    queryFn: getEvents,
  })

  return (
    <main className="mx-auto max-w-2xl px-4 py-8 sm:py-12">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-heading font-semibold tracking-tight text-foreground sm:text-4xl">
          Encuentra tus fotos de carrera
        </h1>
        <p className="mt-2 text-muted-foreground">
          Elige tu carrera y busca con tu número de corredor.
        </p>
      </header>

      {isLoading && (
        <p className="text-center text-muted-foreground">Cargando carreras…</p>
      )}

      {isError && (
        <p className="text-center text-destructive">
          No pudimos cargar las carreras. Intenta de nuevo en un momento.
        </p>
      )}

      {events && events.length === 0 && (
        <p className="text-center text-muted-foreground">
          Todavía no hay carreras publicadas.
        </p>
      )}

      <ul className="flex flex-col gap-3">
        {events?.map((event) => (
          <li key={event.id}>
            <Link to={`/eventos/${event.slug}`}>
              <Card className="transition-colors hover:ring-primary/40">
                <CardHeader>
                  <CardTitle className="text-lg">{event.name}</CardTitle>
                </CardHeader>
                {(event.event_date || event.location) && (
                  <CardContent className="text-sm text-muted-foreground">
                    {[formatDate(event.event_date), event.location]
                      .filter(Boolean)
                      .join(' · ')}
                  </CardContent>
                )}
              </Card>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  )
}
