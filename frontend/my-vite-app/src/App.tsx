import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'

import LoginPage from './pages/login'
import RegisterPage from './pages/register'
import LobbyPage from './pages/lobbies'
import LobbyApprovedPage from './pages/lobbyapproved'
import NavigationPage from './pages/navigation'

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
      <Route
        path="/matches/:match_id/navigation"
        element={
          <Layout>
            <NavigationPage />
          </Layout>
        }
      />
      <Route
        path="/matches/:match_id/completed"
        element={
          <Layout>
            <NavigationPage />
          </Layout>
        }
    </Routes>
  )
}



