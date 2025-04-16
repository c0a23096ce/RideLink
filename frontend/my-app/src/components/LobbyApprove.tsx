// components/LobbyApprove.tsx
'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/apiClient';
import { UserCardList } from './card';
import { LobbyUser } from './card/UserCard';
import { Box, Button } from '@mui/material';
import { useRouter } from 'next/navigation';
import { useSocket } from '@/contexts/WebSocketContext';

export default function LobbyUserPage() {
  const router = useRouter();
  const socket = useSocket();
  const { lobby_id } = useParams();
  const [user, setUser] = useState<any>(null);
  const [users, setUsers] = useState<LobbyUser[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await apiClient.get('/user/me');
        setUser(res.data);
      } catch (err) {
        console.error('ユーザー情報の取得に失敗しました:', err);
      }
    };
    fetchUser();
  }, []);

  useEffect(() => {
    const fetchUsers = async () => {
      console.log('問い合わせるlobby_id:', lobby_id);
      try {
        const res = await apiClient.get(`matching/lobbies/${lobby_id}/users`);
        const formattedUsers = res.data.map((id: number) => ({
          user_id: id,
        }));
        setUsers(formattedUsers);
        console.log('取得したユーザー:', formattedUsers);
      } catch (error) {
        console.error('ユーザー一覧の取得に失敗しました', error);
      } finally {
        setLoading(false);
      }
    };

    if (lobby_id) fetchUsers();
  }, [lobby_id]);

  useEffect(() => {
    if (!socket) return;

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocketメッセージ受信:', data);
      if (data.type === 'lobby_approved') {
        alert(data.message);
        router.push(`/matches/${data.match_id}/navigation`);
      }
    };

    return () => {
      socket.onmessage = null;
    };
  }, [socket, router]);

  const handleApprove = async () => {
    try {
      await apiClient.post(`/matching/lobbies/${lobby_id}/approved`,
        {
          user_id: 2, // 仮のユーザーID
          lobby_id: lobby_id,
        }
      );
      alert('マッチングが承認されました');
    } catch (error) {
      console.error('承認に失敗しました', error);
    }
  };

  const handleCancel = async () => {
    try {
      await apiClient.post(`/matching/lobbies/${lobby_id}/cancel`);
      alert('マッチングをキャンセルしました');
    } catch (error) {
      console.error('キャンセルに失敗しました', error);
    }
  };

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
  );
}

