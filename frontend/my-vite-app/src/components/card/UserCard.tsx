// src/components/card/UserCard.tsx
'use client'

import {
  Card,
  CardContent,
  Typography,
  Grid,
  Rating,
} from '@mui/material'

export type LobbyUser = {
  user_id: number
  average_rating?: number | null
}

export default function UserCard({ user }: { user: LobbyUser }) {
  return (
    <Card sx={{ minWidth: 250 }}>
      <CardContent>
        <Grid container alignItems="center" spacing={2}>
          <Grid item>
            <Typography variant="h6">ユーザーID: {user.user_id}</Typography>
            <Typography variant="body2" color="text.secondary">
              評価：{' '}
              {user.average_rating !== null && user.average_rating !== undefined ? (
                <>
                  <Rating
                    value={user.average_rating}
                    precision={0.1}
                    readOnly
                    size="small"
                  />
                  <Typography variant="caption" component="span" ml={1}>
                    ({user.average_rating.toFixed(1)})
                  </Typography>
                </>
              ) : (
                '未評価'
              )}
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  )
}

