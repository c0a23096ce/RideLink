'use client';

import { Box } from '@mui/material';
import LobbyView from '../../components/LobbyView';
import Sidebar from '../../components/Sidebar';

export default function LobbyPage() {
  const handleCreateLobby = () => {
    alert('ロビー作成画面を開く');
  };

  const handleJoinLobby = () => {
    alert('ロビーに参加する処理を呼び出す');
  };

  return (
    <Box display="flex" height="100vh">
      <Sidebar/>
      <LobbyView
        onCreateLobby={handleCreateLobby}
        onJoinLobby={handleJoinLobby}
      />
    </Box>
  );
}
