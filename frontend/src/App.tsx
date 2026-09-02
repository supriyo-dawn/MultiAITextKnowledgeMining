import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import { KnowledgeProvider } from './context/KnowledgeContext'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'
import Knowledge from './pages/Knowledge'
import Search from './pages/Search'
import Chat from './pages/Chat'

function App() {
  return (
    <KnowledgeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/knowledge" element={<Knowledge />} />
            <Route path="/search" element={<Search />} />
            <Route path="/chat" element={<Chat />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </KnowledgeProvider>
  )
}

export default App
