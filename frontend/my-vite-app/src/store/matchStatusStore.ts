// src/store/matchStatusStore.ts
import { create } from 'zustand'

type MatchStatusState = {
  userId: number | null               // ユーザーID
  status: string | null               // ステータス (例: 'approved')
  setUserId: (userId: number) => void // ユーザーIDをセット
  setStatus: (status: string | null) => void // ステータスをセット
  reset: () => void                   // 状態をリセット
}

export const useMatchStatusStore = create<MatchStatusState>((set) => ({
  userId: null,
  status: null,
  setUserId: (userId) => set({ userId }),
  setStatus: (status) => set({ status }),
  reset: () => set({ userId: null, status: null }),
}))


