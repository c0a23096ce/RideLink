import { Box, Button, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'

export default function Sidebar() {
  const navigate = useNavigate()

  return (
    <Box width="240px" bgcolor="#1e1e1e" color="white" p={2}>
      <Typography variant="h6" gutterBottom>
        メニュー
      </Typography>
      <Button fullWidth sx={{ color: 'white' }} onClick={() => navigate('/lobbies')}>
        ホーム
      </Button>
      <Button fullWidth sx={{ color: 'white' }} onClick={() => navigate('/profile')}>
        プロフィール
      </Button>
    </Box>
  )
}
