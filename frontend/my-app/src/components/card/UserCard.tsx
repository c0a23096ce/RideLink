// components/UserCard.tsx
'use client';

import {
  Card,
  CardContent,
  Typography,
  Avatar,
  Grid,
} from '@mui/material';

export type LobbyUser = {
  id: number;
  name: string;
  role: 'driver' | 'passenger';
};

export default function UserCard({ user }: { user: LobbyUser }) {
  return (
    <Card sx={{ minWidth: 250 }}>
      <CardContent>
        <Grid container alignItems="center" spacing={2}>
          <Grid item>
            <Avatar>{user.name.charAt(0)}</Avatar>
          </Grid>
          <Grid item>
            <Typography variant="h6">{user.name}</Typography>
            <Typography variant="body2" color="text.secondary">
              {user.role === 'driver' ? 'ドライバー' : '乗客'}
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}
