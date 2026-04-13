import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import BlogList from './components/BlogList'
import BlogDetail from './components/BlogDetail'

function App() {
  return (
    <Router>
      <div className="app-layout">
        {/* Fixed left sidebar — always visible */}
        <Sidebar />

        {/* Scrollable right panel — route content */}
        <main className="main-area">
          <Routes>
            <Route path="/"          element={<BlogList />} />
            <Route path="/blog/:id"  element={<BlogDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
