// src/components/StatusWatcher.tsx
import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useMatchStatusStore } from '../store/matchStatusStore'
import apiClient from '../lib/apiClient'

export default function StatusWatcher() {
  const navigate = useNavigate()
  const location = useLocation()
  const status = useMatchStatusStore((s) => s.status)
  const setStatus = useMatchStatusStore((s) => s.setStatus)
  const userId = useMatchStatusStore((s) => s.userId)

  // ✅ 1️⃣ ページ再読込時：サーバーに問い合わせて状態を復元
  useEffect(() => {
    const fetchStatus = async () => {
      if (!userId) return // ユーザーIDがなければ何もしない
      try {
        const res = await apiClient.get(`/matches/${userId}/status`)
        const serverStatus = res.data.status
        console.log('StatusWatcher: サーバーから状態取得:', serverStatus)
        setStatus(serverStatus)
      } catch (err) {
        console.error('状態の問い合わせに失敗', err)
      }
    }
    fetchStatus()
  }, [userId, setStatus])

  // ✅ 2️⃣ 状態が変わったときに画面遷移する
  const routeMap: Record<string, (matchId: string) => string> = {
    idol: () => '/lobbies',
    in_lobby: (matchId) => `/lobbies/${matchId}/approved`,
    navigating: (matchId) => `/matches/${matchId}/navigation`,
    completed: (matchId) => `/matches/${matchId}/completed`,
    // 他のステータスがあればここに追加
  }

  useEffect(() => {
    if (!status) return

    const [state, matchId] = status.split(':')
    const targetPath = routeMap[state]?.(matchId)

    if (
      targetPath &&
      location.pathname !== targetPath &&
      !location.pathname.startsWith('/login') &&
      !location.pathname.startsWith('/register')
    ) {
      console.log(`StatusWatcher: 遷移 → ${targetPath}`)
      navigate(targetPath)
    }
  }, [status, navigate, location])

  return null
}
