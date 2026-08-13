import { Link } from 'react-router-dom'
import { Pencil, Trash2 } from 'lucide-react'
import type { EventWithCount } from '@/types/api'
import { formatEventDate } from '@/lib/format'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { DeleteEventDialog } from './DeleteEventDialog'

interface AdminEventsTableProps {
  events: EventWithCount[]
  onTogglePublish: (event: EventWithCount, next: boolean) => void
  pendingPublishSlug: string | null
  onDelete: (slug: string) => void
  pendingDeleteSlug: string | null
}

export function AdminEventsTable({
  events,
  onTogglePublish,
  pendingPublishSlug,
  onDelete,
  pendingDeleteSlug,
}: AdminEventsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Carrera</TableHead>
          <TableHead>Fecha</TableHead>
          <TableHead>Lugar</TableHead>
          <TableHead className="text-right">Fotos</TableHead>
          <TableHead>Estado</TableHead>
          <TableHead>Publicar</TableHead>
          <TableHead className="text-right">Acciones</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {events.map((event) => (
          <TableRow key={event.id}>
            <TableCell>
              <div className="font-medium text-foreground">{event.name}</div>
              <div className="font-mono text-xs text-muted-foreground">{event.slug}</div>
            </TableCell>
            <TableCell className="text-muted-foreground">
              {formatEventDate(event.event_date) ?? '—'}
            </TableCell>
            <TableCell className="text-muted-foreground">{event.location ?? '—'}</TableCell>
            <TableCell className="text-right tabular-nums">{event.photo_count}</TableCell>
            <TableCell>
              <Badge variant={event.is_published ? 'default' : 'secondary'}>
                {event.is_published ? 'Publicada' : 'Borrador'}
              </Badge>
            </TableCell>
            <TableCell>
              <Switch
                checked={event.is_published}
                disabled={pendingPublishSlug === event.slug}
                onCheckedChange={(checked) => onTogglePublish(event, checked)}
                aria-label={event.is_published ? 'Despublicar' : 'Publicar'}
              />
            </TableCell>
            <TableCell>
              <div className="flex justify-end gap-1">
                <Button
                  variant="ghost"
                  size="icon-sm"
                  nativeButton={false}
                  render={<Link to={`/admin/eventos/${event.slug}`} />}
                  aria-label={`Editar ${event.name}`}
                >
                  <Pencil className="size-4" />
                </Button>
                <DeleteEventDialog
                  slug={event.slug}
                  name={event.name}
                  isPending={pendingDeleteSlug === event.slug}
                  onConfirm={() => onDelete(event.slug)}
                  trigger={
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                      aria-label={`Eliminar ${event.name}`}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  }
                />
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
