import { Route, Routes } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { EventsListPage } from '@/pages/EventsListPage'
import { EventDetailPage } from '@/pages/EventDetailPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<EventsListPage />} />
        <Route path="/eventos/:slug" element={<EventDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
