'use client';
import { Box, Button, Typography } from '@mui/material';
import { useRouter } from 'next/navigation';

export default function Sidebar() {
  const router = useRouter();

  return (
    <Box width="240px" bgcolor="#1e1e1e" color="white" p={2}>
      <Typography variant="h6" gutterBottom>
        メニュー
      </Typography>
      <Button fullWidth sx={{ color: 'white' }} onClick={() => router.push('/lobbies')}>
        ホーム
      </Button>
      <Button fullWidth sx={{ color: 'white' }} onClick={() => router.push('/profile')}>
        プロフィール
      </Button>
    </Box>
  );
}
