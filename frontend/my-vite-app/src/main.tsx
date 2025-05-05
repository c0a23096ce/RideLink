// src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import App from './App'
import { WebSocketProvider } from './contexts/WebSocketContext'
import './index.css'

// MUIのダークテーマ例（必要に応じてカスタム）
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#90caf9' },
    secondary: { main: '#f48fb1' },
  },
  shape: {
    borderRadius: 12,
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  // <React.StrictMode>
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <WebSocketProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </WebSocketProvider>
    </ThemeProvider>
  // </React.StrictMode>
)


