import { useQuery } from '@tanstack/react-query'
import { getAdminStats } from '@/api/client'
import { adminKeys } from '@/lib/adminQueries'
import { StatCard, StatCardSkeleton } from '@/components/admin/StatCard'
import { EmptyBib } from '@/components/EmptyBib'

export function AdminDashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: adminKeys.stats,
    queryFn: getAdminStats,
    retry: false,
  })

  return (
    <div>
      <h1 className="font-heading text-2xl font-bold tracking-tight">Resumen</h1>
      <p className="mt-1 text-sm text-muted-foreground">Estado general del catálogo.</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {isLoading &&
          [0, 1, 2].map((i) => <StatCardSkeleton key={i} />)}

        {isError && (
          <div className="col-span-full flex flex-col items-center py-10 text-center">
            <EmptyBib label="!" />
            <h2 className="mt-6 font-heading text-lg font-bold">No pudimos cargar el resumen</h2>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Revisa tu conexión y vuelve a intentar.
            </p>
          </div>
        )}

        {data && (
          <>
            <StatCard
              label="Carreras"
              value={data.events_total}
              detail={`${data.events_published} publicadas · ${data.events_draft} borradores`}
            />
            <StatCard label="Publicadas" value={data.events_published} />
            <StatCard label="Fotos" value={data.photos_total} />
          </>
        )}
      </div>
    </div>
  )
}
