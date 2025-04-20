import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'

import LoginPage from './pages/login'
import RegisterPage from './pages/register'
import LobbyPage from './pages/lobbies'
import LobbyApprovedPage from './pages/lobbyapproved'

export default function App() {
  return (
    <Routes>
      {/* Layoutなしページ */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Layoutありページ（Sidebarつき） */}
      <Route
        path="/"
        element={
          <Layout>
            <LobbyPage />
          </Layout>
        }
      />
      <Route
        path="/lobbies"
        element={
          <Layout>
            <LobbyPage />
          </Layout>
        }
      />
      <Route
        path="/lobbies/:lobby_id/approved"
        element={
          <Layout>
            <LobbyApprovedPage />
          </Layout>
        }
      />
    </Routes>
  )
}



