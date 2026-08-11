import { Route, Routes } from 'react-router-dom'
import { EventsListPage } from '@/pages/EventsListPage'
import { EventDetailPage } from '@/pages/EventDetailPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<EventsListPage />} />
      <Route path="/eventos/:slug" element={<EventDetailPage />} />
    </Routes>
  )
}
