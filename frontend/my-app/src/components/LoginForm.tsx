// src/components/LoginForm.tsx
'use client';
import { useState } from 'react';
import { Button, TextField, Box, Typography, Paper } from '@mui/material';
import apiClient from '../lib/apiClient';
import { useRouter } from 'next/navigation';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  const handleLogin = async () => {
    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);
      formData.append("grant_type", "password");
      
      console.log("送信データ:", formData.toString());

      const response = await apiClient.post("/user/login", 
        formData,
        {
          headers: {
            "Content-Type": "application/x-www-form-urlencoded"
          }
        }
      );

      localStorage.setItem('token', response.data.access_token);
      router.push('/lobbies');
    } catch (error) {
      alert('ログインに失敗しました。');
      console.error(error);
    }
  };

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
    >
      <Paper elevation={6} sx={{ p: 5, width: 360 }}>
        <Typography variant="h5" mb={3} textAlign="center">
          ログイン
        </Typography>
        <TextField
          label="メールアドレス"
          variant="outlined"
          fullWidth
          margin="normal"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <TextField
          label="パスワード"
          type="password"
          variant="outlined"
          fullWidth
          margin="normal"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button
          variant="contained"
          color="primary"
          fullWidth
          sx={{ mt: 2 }}
          onClick={handleLogin}
        >
          ログイン
        </Button>
        <Button
          variant="outlined"
          color="secondary"
          fullWidth
          sx={{ mt: 2 }}
          onClick={() => router.push('/register')} // 登録画面のルートに遷移
        >
          新規登録
        </Button>
      </Paper>
    </Box>
  );
}
