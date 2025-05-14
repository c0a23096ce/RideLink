/// src/stores/useAppStore.ts

import { create } from 'zustand'

export type UserStatus =
  | 'searching'
  | 'in_lobby'
  | 'approved'
  | 'matched'
  | 'navigating'
  | 'completed'

interface AppState {
  userStatus: UserStatus
  lastStatusPath: string | null
  setUserStatus: (status: UserStatus) => void
  setLastStatusPath: (path: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  userStatus: 'searching',
  lastStatusPath: null,
  setUserStatus: (status) => set({ userStatus: status }),
  setLastStatusPath: (path) => set({ lastStatusPath: path }),
}))