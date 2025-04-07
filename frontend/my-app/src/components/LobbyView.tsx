// components/LobbyView.tsx
'use client';

import {
  Box,
  Button,
  Dialog,
  DialogContent,
  IconButton,
  TextField,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import apiClient from '../lib/apiClient';
import { useRouter } from 'next/navigation';

const MapSection = dynamic(() => import('./MapSection'), { ssr: false });

export default function LobbyView({ onCreateLobby, onJoinLobby }: {
  onCreateLobby: () => void;
  onJoinLobby: () => void;
}) {
  const router = useRouter();
  const [openMap, setOpenMap] = useState(false);
  const [isJoining, setIsJoining] = useState(false);
  const [searchOrigin, setSearchOrigin] = useState('');
  const [searchDest, setSearchDest] = useState('');
  const [destination, setDestination] = useState<[number, number] | null>(null);
  const [origin, setOrigin] = useState<[number, number] | null>(null);
  const [user, setUser] = useState<any>(null);
  const [focus, setFocus] = useState<'origin' | 'destination'>('origin');
  const [lobbyId, setLobbyId] = useState('');

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

  const handleGeolocate = () => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const coords: [number, number] = [position.coords.latitude, position.coords.longitude];
        setOrigin(coords);
      },
      (error) => {
        console.error('現在地の取得に失敗しました:', error);
      }
    );
  };

  const handleSearch = async () => {
    const query = focus === 'origin' ? searchOrigin : searchDest;
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`
    );
    const data = await res.json();
    if (data && data.length > 0) {
      const lat = parseFloat(data[0].lat);
      const lon = parseFloat(data[0].lon);
      if (focus === 'origin') {
        setOrigin([lat, lon]);
      } else {
        setDestination([lat, lon]);
      }
    } else {
      alert('場所が見つかりませんでした');
    }
  };

  const handleSubmitLocation = async () => {
    if (!origin || !destination) return;
    try {
      if (isJoining) {
        const lobby = await apiClient.post(`/matching/join_lobby`, {
          passenger_id: 2, // 仮のユーザーID
          passenger_location: [origin[0], origin[1]],
          passenger_destination: [destination[0], destination[1]],
        });
        alert('ロビーに参加しました');
        console.log(lobby);
        router.push(`/lobbies/${lobby.data.lobby.lobby_id}`);
      } else {
        const lobby = await apiClient.post('/matching/lobbies', {
          driver_id: 1, // 仮のユーザーID
          driver_location: [origin[0], origin[1]],
          destination: [destination[0], destination[1]]
        });
        alert('ロビーを作成しました');
        router.push(`/lobbies/${lobby.data.lobby_id}`);
      }
      setOpenMap(false);
    } catch (err) {
      alert('送信に失敗しました');
      console.error(err);
    }
  };

  const openCreateDialog = () => {
    setIsJoining(false);
    setOpenMap(true);
  };

  const openJoinDialog = () => {
    setIsJoining(true);
    setOpenMap(true);
  };

  return (
    <Box
      flex={1}
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
      height="100vh"
    >
      <Box display="flex" gap={4}>
        <Button
          variant="outlined"
          sx={{ borderRadius: 1 }}
          onClick={openCreateDialog}
        >
          ⚡ マッチングロビーの作成
        </Button>
        <Button
          variant="outlined"
          sx={{ borderRadius: 1 }}
          onClick={openJoinDialog}
        >
          ⚡ マッチングへの参加
        </Button>
      </Box>

      {/* マップオーバーレイ */}
      <Dialog open={openMap} onClose={() => setOpenMap(false)} fullScreen>
        <DialogContent sx={{ p: 2, position: 'relative' }}>
          <IconButton
            onClick={() => setOpenMap(false)}
            sx={{ position: 'absolute', top: 10, right: 10, zIndex: 999, color: 'white' }}
          >
            <CloseIcon />
          </IconButton>

          <Box display="flex" gap={2} mb={2}>
            <TextField
              label="出発地を検索"
              variant="outlined"
              fullWidth
              value={searchOrigin}
              onChange={(e) => setSearchOrigin(e.target.value)}
              onFocus={() => setFocus('origin')}
            />
            <TextField
              label="目的地を検索"
              variant="outlined"
              fullWidth
              value={searchDest}
              onChange={(e) => setSearchDest(e.target.value)}
              onFocus={() => setFocus('destination')}
            />
            <Button variant="contained" onClick={handleSearch}>検索</Button>
            <Button variant="outlined" onClick={handleGeolocate}>現在地</Button>
          </Box>

          <Box height="70vh">
            <MapSection origin={origin} destination={destination} focus={focus} />
          </Box>

          <Box mt={2} textAlign="right">
            <Button
              variant="contained"
              color="primary"
              onClick={handleSubmitLocation}
              disabled={!destination || !origin}
            >
              {isJoining ? 'この条件で参加' : 'この場所でロビーを作成'}
            </Button>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
}



