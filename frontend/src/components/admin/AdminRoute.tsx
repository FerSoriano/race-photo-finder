import { Suspense } from 'react'
import { Outlet } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useAdminKey } from '@/lib/adminAuth'
import { AdminLoginPage } from '@/pages/admin/AdminLoginPage'
import { AdminLayout } from '@/components/admin/AdminLayout'

/**
 * Gate for the whole /admin subtree. No valid key -> the paste screen, not a
 * redirect to "/" -- a bookmarked /admin must still land on /admin.
 *
 * The dashboard/events/edit pages are lazy-loaded (see App.tsx), so this
 * Suspense boundary is what shows while one of those chunks fetches.
 */
export function AdminRoute() {
  const key = useAdminKey()

  if (!key) return <AdminLoginPage />

  return (
    <AdminLayout>
      <Suspense fallback={<AdminPageFallback />}>
        <Outlet />
      </Suspense>
    </AdminLayout>
  )
}

function AdminPageFallback() {
  return (
    <div className="flex items-center justify-center py-24 text-muted-foreground">
      <Loader2 className="size-5 animate-spin" />
    </div>
  )
}
