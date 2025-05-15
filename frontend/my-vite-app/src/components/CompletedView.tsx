// src/components/CompletedView.tsx
import { Box, Typography, Grid, Button } from '@mui/material'
import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import apiClient from '../lib/apiClient'
import { useMatchStatusStore } from '../store/matchStatusStore'
import UserCard from './card/ReviewUserCard'

interface UserData {
  user_id: number
  // user_name: string
}

export default function CompletedView() {
  const { match_id } = useParams()
  const reviewerId = useMatchStatusStore((s) => s.userId)
  const [users, setUsers] = useState<UserData[]>([])
  const [ratings, setRatings] = useState<Record<number, number>>({})
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const fetchUsers = async () => {
      if (!match_id || !reviewerId) return
      try {
        const res = await apiClient.get(`/matches/${match_id}/review-targets/${reviewerId}`)
        const filtered = res.data.data.users.filter((u: UserData) => u.user_id !== reviewerId)
        setUsers(filtered)
      } catch (err) {
        console.error('参加ユーザーの取得に失敗:', err)
      }
    }
    fetchUsers()
  }, [match_id, reviewerId])

  const handleRatingChange = (userId: number, value: number | null) => {
    if (value === null) return
    setRatings((prev) => ({ ...prev, [userId]: value }))
  }

  const allValid =
    Object.keys(ratings).length === users.length &&
    Object.values(ratings).every((v) => v >= 1 && v <= 5)

  const handleSubmit = async () => {
    if (!match_id) return
    const invalid = Object.values(ratings).some((v) => v < 1 || v > 5)
    if (invalid) {
      alert('すべての評価は1〜5の範囲で入力してください')
      return
    }

    setSubmitting(true)
    try {
      await apiClient.patch(`/matches/${match_id}/review-targets/${reviewerId}`, {
        match_id: Number(match_id),
        user_id: reviewerId,
        ratings,
      })
      alert('評価を送信しました')
    } catch (err) {
      console.error('評価の送信に失敗:', err)
      alert('評価送信に失敗しました')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box flex={1} p={4}>
      <Typography variant="h5" gutterBottom>
        乗り合わせたユーザーを評価してください
      </Typography>
      <Grid container spacing={2}>
        {users.map((user) => (
          <Grid item xs={12} sm={6} md={4} key={user.user_id}>
            <UserCard
              userId={user.user_id}
              // userName={user.user_name || `ユーザー${user.user_id}`}
              rating={ratings[user.user_id] || null}
              onRatingChange={handleRatingChange}
            />
          </Grid>
        ))}
      </Grid>
      <Box mt={4} textAlign="center">
        <Button
          variant="contained"
          color="primary"
          onClick={handleSubmit}
          disabled={submitting || !allValid}
        >
          全員の評価を送信
        </Button>
      </Box>
    </Box>
  )
}
