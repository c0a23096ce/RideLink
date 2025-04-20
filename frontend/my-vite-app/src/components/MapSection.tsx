// src/components/MapSection.tsx
import { Box } from '@mui/material'

export default function MapSection({
  origin,
  destination,
  focus,
}: {
  origin: [number, number] | null
  destination: [number, number] | null
  focus: 'origin' | 'destination'
}) {
  return (
    <Box
      height="100%"
      bgcolor="#ddd"
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
    >
      <p>🗺️ MapSection（仮の表示）</p>
      <p>出発地: {origin ? origin.join(', ') : '未設定'}</p>
      <p>目的地: {destination ? destination.join(', ') : '未設定'}</p>
      <p>現在の入力: {focus}</p>
    </Box>
  )
}
