// src/pages/navigation.tsx
import { Box } from '@mui/material'
import NavigationView from '../components/NavigationView'
import FullScreenView from '../components/FullScreenView'

export default function NavigationPage() {
  return (
    <Box display="flex" height="100vh">
      <NavigationView />
    </Box>
  )
}