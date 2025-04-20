// src/contexts/WebSocketContext.tsx
import { createContext, useContext, useEffect, useState } from 'react'

const WebSocketContext = createContext<WebSocket | null>(null)

export const WebSocketProvider = ({ children }: { children: React.ReactNode }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws?user_id=2') // ← ユーザーIDは動的でもOK
    setSocket(ws)

    ws.onopen = () => {
      console.log('✅ WebSocket 接続完了')
    }

    ws.onclose = () => {
      console.log('❌ WebSocket 接続終了')
    }

    ws.onerror = (err) => {
      console.error('⚠️ WebSocket エラー:', err)
    }

    return () => {
      ws.close()
    }
  }, [])

  return (
    <WebSocketContext.Provider value={socket}>
      {children}
    </WebSocketContext.Provider>
  )
}

export const useSocket = () => useContext(WebSocketContext)

  