// src/store/matchStatusStore.ts
import { create } from 'zustand'

type MatchStatusState = {
  userId: number | null
  status: string | null      // e.g. 'in_lobby'
  matchId: string | null     // e.g. '123'
  setUserId: (userId: number) => void
  setStatus: (status: string | null) => void
  setMatchId: (matchId: string | null) => void
  setStatusAndMatchId: (status: string, matchId: string) => void
  reset: () => void
}

export const useMatchStatusStore = create<MatchStatusState>((set) => ({
  userId: 2,
  status: null,
  matchId: null,
  setUserId: (userId) => set({ userId }),
  setStatus: (status) => set({ status }),
  setMatchId: (matchId) => set({ matchId }),
  setStatusAndMatchId: (status, matchId) => set({ status, matchId }),
  reset: () => set({ userId: null, status: null, matchId: null }),
}))






