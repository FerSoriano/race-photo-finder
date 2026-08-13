import { Link } from 'react-router-dom'
import type { EventRead } from '@/types/api'
import { EventCover } from '@/components/EventCover'
import { Skeleton } from '@/components/ui/skeleton'
import { formatEventMeta } from '@/lib/format'

interface EventCardProps {
  event: EventRead
}

export function EventCard({ event }: EventCardProps) {
  const meta = formatEventMeta(event.event_date, event.location)

  return (
    <Link
      to={`/eventos/${event.slug}`}
      className="group block overflow-hidden rounded-lg border border-border bg-card transition-[transform,border-color] duration-150 hover:-translate-y-0.5 hover:border-muted-foreground/40 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none active:translate-y-0 motion-reduce:hover:translate-y-0"
    >
      <EventCover slug={event.slug} coverUrl={event.cover_url} className="aspect-video" />
      <div className="flex flex-col gap-1 px-4 pt-3.5 pb-4">
        <h2 className="font-heading text-[1.0625rem] leading-tight font-bold tracking-tight text-balance">
          {event.name}
        </h2>
        {meta && <p className="text-[0.8125rem] tabular-nums text-muted-foreground">{meta}</p>}
      </div>
    </Link>
  )
}

/** Same shape as the card, so the grid doesn't jump when data lands. */
export function EventCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card">
      <Skeleton className="aspect-video rounded-none" />
      <div className="flex flex-col gap-2 px-4 pt-4 pb-5">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  )
}
