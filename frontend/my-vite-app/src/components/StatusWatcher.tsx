// src/components/StatusWatcher.tsx
import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useMatchStatusStore } from '../store/matchStatusStore'
import { useRestoreMatchStatus } from '../hooks/useRestoreMatchStatus'

export default function StatusWatcher() {
  const navigate = useNavigate()
  const location = useLocation()
  const status = useMatchStatusStore((s) => s.status)
  const matchId = useMatchStatusStore((s) => s.matchId)
  const userId = useMatchStatusStore((s) => s.userId)

  useEffect(() => {
    const restore = async () => {
      await useRestoreMatchStatus(userId)
    }
    restore()
  }, [userId])

  const routeMap: Record<string, (matchId: string) => string> = {
    idol: () => '/lobbies',
    in_lobby: (matchId) => `/lobbies/${matchId}/approved`,
    navigating: (matchId) => `/matches/${matchId}/navigation`,
    completed: (matchId) => `/matches/${matchId}/completed`,
  }

  useEffect(() => {
    if (!status || (status !== 'idol' && !matchId)) return // matchId が必要な状態をガード
    const targetPath = routeMap[status]?.(matchId as string) // matchId が null でないことを保証

    if (
      targetPath &&
      location.pathname !== targetPath &&
      !location.pathname.startsWith('/login') &&
      !location.pathname.startsWith('/register')
    ) {
      console.log(`StatusWatcher: 遷移 → ${targetPath}`)
      navigate(targetPath, { replace: true })
    }
  }, [status, matchId, navigate, location])

  return null
}





