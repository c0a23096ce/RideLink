// src/hooks/useRestoreMatchStatus.ts
import { useMatchStatusStore } from '../store/matchStatusStore'
import apiClient from '../lib/apiClient'

export const useRestoreMatchStatus = async (userId: number | null): Promise<void> => {
  const setStatusAndMatchId = useMatchStatusStore.getState().setStatusAndMatchId

  if (!userId) {
    console.warn('useRestoreMatchStatus: userIdがnullなので中断')
    return
  }

  try {
    const res1 = await apiClient.get(`/matches/${userId}`)
    const matchId = res1.data.match_id

    const res2 = await apiClient.get(`/matches/${userId}/status`)
    const state = res2.data.status

    console.log('useRestoreMatchStatus: status =', state, 'matchId =', matchId)
    setStatusAndMatchId(state, matchId)
  } catch (err) {
    console.error('useRestoreMatchStatus: 復元に失敗', err)
    useMatchStatusStore.getState().reset()
  }
}





