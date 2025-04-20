import { useState } from 'react'
import { Box, Button, Paper, TextField, Typography } from '@mui/material'
import apiClient from '../lib/apiClient'
import { useNavigate } from 'react-router-dom'

export default function RegisterForm() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const handleRegister = async () => {
    try {
      await apiClient.post('/user/register', {
        name,
        email,
        phone,
        password,
      })
      alert('登録が完了しました！ログインしてください。')
      navigate('/login')
    } catch (error) {
      alert('登録に失敗しました。')
      console.error(error)
    }
  }

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
      <Paper elevation={6} sx={{ p: 5, width: 360 }}>
        <Typography variant="h5" mb={3} textAlign="center">
          新規登録
        </Typography>
        <TextField
          label="名前"
          variant="outlined"
          fullWidth
          margin="normal"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <TextField
          label="メールアドレス"
          variant="outlined"
          fullWidth
          margin="normal"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <TextField
          label="電話番号"
          variant="outlined"
          fullWidth
          margin="normal"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
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
          onClick={handleRegister}
        >
          登録する
        </Button>
      </Paper>
    </Box>
  )
}
