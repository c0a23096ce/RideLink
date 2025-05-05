// src/components/Layout.tsx
import { Box } from '@mui/material'
import Sidebar from './Sidebar'
import { ReactNode } from 'react'
import StatusWatcher from './StatusWatcher'  // ✅ 追加

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <Box display="flex" height="100vh">
      <Sidebar />
      <Box flex={1} overflow="auto">
        <StatusWatcher />  {/* ✅ 状態監視を追加 */}
        {children}
      </Box>
    </Box>
  )
}

