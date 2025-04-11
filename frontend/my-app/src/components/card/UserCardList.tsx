'use client';

import { Grid } from '@mui/material';
import UserCard, { LobbyUser } from './UserCard';

export default function UserCardList({ users }: { users: LobbyUser[] }) {
  return (
    <Grid container spacing={2}>
      {users.map((user) => (
        <Grid item key={user.user_id}>
          <UserCard user={user} />
        </Grid>
      ))}
    </Grid>
  );
}
