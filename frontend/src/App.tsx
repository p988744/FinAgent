import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MainLayout } from './layouts/MainLayout'
import { QueryPage } from './pages/QueryPage'
import { ConfigPage } from './pages/ConfigPage'
import { ModelsPage } from './pages/ModelsPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { WikiPage } from './pages/WikiPage'
import { DocumentDetailPage } from './pages/DocumentDetailPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Navigate to="/query" replace />} />
            <Route path="query" element={<QueryPage />} />
            <Route path="wiki" element={<WikiPage />} />
            <Route path="wiki/document/:docId" element={<DocumentDetailPage />} />
            <Route path="config" element={<ConfigPage />} />
            <Route path="models" element={<ModelsPage />} />
            <Route path="documents" element={<DocumentsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
