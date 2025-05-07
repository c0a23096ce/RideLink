// src/hooks/useRestoreMatchStatus.ts
import { useMatchStatusStore } from '../store/matchStatusStore'
import apiClient from '../lib/apiClient'

/**
 * サーバーからマッチIDとステータスを復元してstoreに反映する共通関数
 */
export const useRestoreMatchStatus = async (userId: number | null) => {
  const setStatus = useMatchStatusStore.getState().setStatus
  const setMatchId = useMatchStatusStore.getState().setMatchId

  if (!userId) {
    console.warn('useRestoreMatchStatus: userIdがnullなので中断')
    return
  }

  try {
    const res1 = await apiClient.get(`/matches/${userId}`)
    const currentMatchId = res1.data.match_id
    console.log('useRestoreMatchStatus: 現在のmatch_id:', currentMatchId)
    setMatchId(currentMatchId)

    const res2 = await apiClient.get(`/matches/${userId}/status`)
    const currentStatus = res2.data.status
    console.log('useRestoreMatchStatus: 現在のstatus:', currentStatus)
    setStatus(currentStatus)
  } catch (err) {
    console.error('useRestoreMatchStatus: 復元に失敗', err)
    setStatus(null)
    setMatchId(null)
  }
}




