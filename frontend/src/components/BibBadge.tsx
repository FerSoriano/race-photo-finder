import { cn } from '@/lib/utils'

interface BibBadgeProps {
  number: string
  /** The detector read this number with low confidence. */
  uncertain?: boolean
  className?: string
}

/**
 * The signature bib at tile scale, carrying the number the detector read.
 *
 * An uncertain read goes amber, never red: the runner has not hit an error,
 * they have hit a maybe -- and the recovery path is right there in
 * "¿Eres tú?".
 */
export function BibBadge({ number, uncertain = false, className }: BibBadgeProps) {
  return (
    <span
      className={cn(
        'relative inline-flex items-center rounded-[3px] px-1.5 pt-0.5 pb-1',
        'font-heading text-xs leading-none font-extrabold tabular-nums',
        'tracking-tight shadow-sm',
        uncertain ? 'bg-warning text-warning-foreground' : 'bg-dorsal text-dorsal-ink',
        className,
      )}
      title={uncertain ? 'Este número no se leyó con total certeza' : undefined}
    >
      {number}
      <span
        className="bib-perforation absolute inset-x-1 bottom-[2px] h-[1px]"
        style={{ '--perf-dash': '2px' } as React.CSSProperties}
      />
    </span>
  )
}
