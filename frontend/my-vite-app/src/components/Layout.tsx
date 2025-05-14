// src/components/Layout.tsx
import { Box } from '@mui/material'
import Sidebar from './Sidebar'
import { ReactNode } from 'react'

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <Box display="flex" height="100vh">
      <Sidebar />
      <Box flex={1} overflow="auto">
        {children}
      </Box>
    </Box>
  )
}

