import { cn } from '@/lib/utils'

interface EmptyBibProps {
  /** What's written on the blank bib. Keep it to a few characters. */
  label?: string
  className?: string
}

/**
 * A blank bib -- nothing written on it yet. Carries every empty state in the
 * app so a dead end still looks like part of the product instead of a line of
 * muted text.
 */
export function EmptyBib({ label = '?', className }: EmptyBibProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'relative grid h-24 w-36 place-items-center rounded-xl border-2',
        'border-dashed border-border bg-card text-muted-foreground',
        className,
      )}
    >
      <span className="bib-pin absolute top-2.5 left-2.5 size-1.5" />
      <span className="bib-pin absolute top-2.5 right-2.5 size-1.5" />
      <span className="font-heading text-3xl font-extrabold tabular-nums opacity-45">
        {label}
      </span>
      <span className="bib-perforation absolute inset-x-7 bottom-2.5 h-[2px]" />
    </div>
  )
}
