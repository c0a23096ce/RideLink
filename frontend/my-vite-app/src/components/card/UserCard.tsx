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
  user_id: number;
};

export default function UserCard({ user }: { user: LobbyUser }) {
  return (
    <Card sx={{ minWidth: 250 }}>
      <CardContent>
        <Grid container alignItems="center" spacing={2}>
          <Grid item>
            <Typography variant="h6">{user.user_id}</Typography>
            <Typography variant="body2" color="text.secondary">
              "ユーザーロール"
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}
