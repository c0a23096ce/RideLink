// src/components/card/ReviewUserCard.tsx
import { Paper, Typography, Rating } from '@mui/material'

type Props = {
  userId: number
  // userName: string
  rating: number | null
  onRatingChange: (userId: number, rating: number | null) => void
}

export default function UserCard({ userId, /* userName, */ rating, onRatingChange }: Props) {
  return (
    <Paper elevation={2} sx={{ p: 2 }}>
      <Typography>{/*userName*/ userId}</Typography>
      <Rating
        name={`rating-${userId}`}
        value={rating}
        onChange={(_, value) => onRatingChange(userId, value)}
      />
    </Paper>
  )
}
