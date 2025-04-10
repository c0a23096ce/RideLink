'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/apiClient';
import { UserCardList } from './card';
import { LobbyUser } from './card/UserCard';

export default function LobbyUserPage() {
  const { lobby_id } = useParams();
  const [users, setUsers] = useState<LobbyUser[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await apiClient.get(`/matching/${lobby_id}/approved`);
        setUsers(res.data);
      } catch (error) {
        console.error('ユーザー一覧の取得に失敗しました', error);
      } finally {
        setLoading(false);
      }
    };

    if (lobby_id) fetchUsers();
  }, [lobby_id]);

  return (
    <main style={{ padding: '2rem' }}>
      <h1>ロビーID: {lobby_id}</h1>
      {loading ? (
        <p>読み込み中...</p>
      ) : users.length > 0 ? (
        <UserCardList users={users} />
      ) : (
        <p>ユーザーがいません。</p>
      )}
    </main>
  );
}

