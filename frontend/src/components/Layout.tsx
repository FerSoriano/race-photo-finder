import { Link, Outlet, useLocation } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'

/**
 * The app shell. Before this existed there was no way back to the event list
 * from a race except the browser's back button.
 *
 * The header spends no Volt: the accent is reserved for the one action on
 * each screen, so the mark carries the bib motif in white instead.
 */
export function Layout() {
  const isHome = useLocation().pathname === '/'

  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur-md backdrop-saturate-150">
        <div className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-3">
          {!isHome && (
            <Link
              to="/"
              aria-label="Volver a las carreras"
              className="-ml-1.5 rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
            >
              <ChevronLeft className="size-5" />
            </Link>
          )}
          <Link
            to="/"
            className="flex items-center gap-2 rounded-md focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            <BibMark />
            <span className="font-heading text-[0.8125rem] font-bold tracking-[0.14em] uppercase">
              Fotos de carrera
            </span>
          </Link>
        </div>
      </header>

      <Outlet />
    </div>
  )
}

/** The signature bib, shrunk to a logo. Exported so the admin shell can reuse
 * the same wordmark instead of duplicating it. */
export function BibMark() {
  return (
    <span className="relative grid h-[22px] w-[30px] flex-none place-items-center rounded-[3px] bg-dorsal text-dorsal-ink">
      <span className="bib-pin absolute top-[3px] left-[3px] size-[2.5px]" />
      <span className="bib-pin absolute top-[3px] right-[3px] size-[2.5px]" />
      <span className="mb-px font-heading text-[0.625rem] leading-none font-extrabold tabular-nums">
        21
      </span>
      <span
        className="bib-perforation absolute inset-x-[3px] bottom-[2px] h-px"
        style={{ '--perf-dash': '2px' } as React.CSSProperties}
      />
    </span>
  )
}
