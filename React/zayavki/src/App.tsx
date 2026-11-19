import { Route, Routes } from 'react-router'
import Header from './components/Header'
import BoardPage from './pages/BoardPage'
import StatsPage from './pages/StatsPage'
import RequestPage from './pages/RequestPage'
import NotFoundPage from './pages/NotFoundPage'
import { useBoard } from './board'

function App() {
  const { notice } = useBoard()

  return (
    <>
      <Header />
      {notice !== '' && <p className="notice notice--page" role="status">{notice}</p>}
      <Routes>
        <Route path="/" element={<BoardPage />} />
        <Route path="/stats" element={<StatsPage />} />
        <Route path="/requests/:id" element={<RequestPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </>
  )
}

export default App
