// src/components/LobbyApprove.tsx
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import apiClient from '../lib/apiClient'
import { UserCardList } from './card'
import { LobbyUser } from './card/UserCard'
import { Box, Button } from '@mui/material'
import { useMatchStatusStore } from '../store/matchStatusStore'

export default function LobbyUserPage() {
  const { lobby_id } = useParams()
  const [users, setUsers] = useState<LobbyUser[]>([])
  const [loading, setLoading] = useState(true)
  const userId = useMatchStatusStore((s) => s.userId)

  useEffect(() => {
    const fetchUsers = async () => {
      if (!lobby_id) return
      console.log('問い合わせるlobby_id:', lobby_id)
      try {
        const res = await apiClient.get(`/matching/lobbies/${lobby_id}/users`)
        const formattedUsers = res.data.map((id: number) => ({
          user_id: id,
        }))
        setUsers(formattedUsers)
        console.log('取得したユーザー:', formattedUsers)
      } catch (error) {
        console.error('ユーザー一覧の取得に失敗しました', error)
      } finally {
        setLoading(false)
      }
    }

    fetchUsers()
  }, [lobby_id])

  const handleApprove = async () => {
    try {
      await apiClient.post(`/matching/lobbies/${lobby_id}/approved`, {
        user_id: userId, // 仮のユーザーID
        lobby_id,
      })
      alert('マッチングが承認されました')
    } catch (error) {
      console.error('承認に失敗しました', error)
    }
  }

  const handleCancel = async () => {
    try {
      await apiClient.post(`/matching/lobbies/${lobby_id}/cancel`)
      alert('マッチングをキャンセルしました')
    } catch (error) {
      console.error('キャンセルに失敗しました', error)
    }
  }

  return (
    <main style={{ padding: '2rem' }}>
      <h1>ロビーID: {lobby_id}</h1>
      {loading ? (
        <p>読み込み中...</p>
      ) : users.length > 0 ? (
        <>
          <UserCardList users={users} />
          <Box mt={4} display="flex" gap={2}>
            <Button variant="contained" color="primary" onClick={handleApprove}>
              承認
            </Button>
            <Button variant="outlined" color="error" onClick={handleCancel}>
              キャンセル
            </Button>
          </Box>
        </>
      ) : (
        <p>ユーザーがいません。</p>
      )}
    </main>
  )
}

