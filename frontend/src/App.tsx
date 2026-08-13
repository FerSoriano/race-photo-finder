import { lazy } from 'react'
import { Route, Routes } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { EventsListPage } from '@/pages/EventsListPage'
import { EventDetailPage } from '@/pages/EventDetailPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

// The panel is only ever opened by the photographer, so it stays out of the
// bundle a runner downloads over mobile data on a WhatsApp link.
const AdminRoute = lazy(() =>
  import('@/components/admin/AdminRoute').then((m) => ({ default: m.AdminRoute })),
)
const AdminDashboardPage = lazy(() =>
  import('@/pages/admin/AdminDashboardPage').then((m) => ({ default: m.AdminDashboardPage })),
)
const AdminEventsPage = lazy(() =>
  import('@/pages/admin/AdminEventsPage').then((m) => ({ default: m.AdminEventsPage })),
)
const AdminEventEditPage = lazy(() =>
  import('@/pages/admin/AdminEventEditPage').then((m) => ({ default: m.AdminEventEditPage })),
)

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<EventsListPage />} />
        <Route path="/eventos/:slug" element={<EventDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      <Route path="/admin" element={<AdminRoute />}>
        <Route index element={<AdminDashboardPage />} />
        <Route path="eventos" element={<AdminEventsPage />} />
        <Route path="eventos/:slug" element={<AdminEventEditPage />} />
      </Route>
    </Routes>
  )
}
