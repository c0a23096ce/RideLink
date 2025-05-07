// src/store/matchStatusStore.ts
import { create } from 'zustand'

type MatchStatusState = {
  userId: number | null
  status: string | null
  matchId: string | null      // matchIdを保存
  setUserId: (userId: number) => void
  setStatus: (status: string | null) => void
  setMatchId: (matchId: string | null) => void
  reset: () => void
}

export const useMatchStatusStore = create<MatchStatusState>((set) => ({
  userId: 2, // テスト用に初期値を設定
  status: null,
  matchId: null,
  setUserId: (userId) => set({ userId }),
  setStatus: (status) => set({ status }),
  setMatchId: (matchId) => set({ matchId }),
  reset: () => set({ userId: null, status: null, matchId: null }),
}))



