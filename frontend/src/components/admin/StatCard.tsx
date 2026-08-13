import type { ReactNode } from 'react'
import { Skeleton } from '@/components/ui/skeleton'

interface StatCardProps {
  label: string
  value: ReactNode
  detail?: ReactNode
}

/**
 * A hand-rolled tile rather than shadcn's `card` -- STATUS.md records `card`
 * as deliberately removed scaffold residue, and this is the only place a
 * bordered surface is needed.
 */
export function StatCard({ label, value, detail }: StatCardProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{label}</p>
      <p className="mt-2 font-heading text-3xl font-extrabold tabular-nums">{value}</p>
      {detail && <p className="mt-1 text-sm text-muted-foreground">{detail}</p>}
    </div>
  )
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="mt-3 h-8 w-16" />
    </div>
  )
}
