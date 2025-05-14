// src/contexts/WebSocketContext.tsx
import { createContext, useContext, useEffect, useState } from 'react'
import { useMatchStatusStore } from '../store/matchStatusStore'
import { useRestoreMatchStatus } from '../hooks/useRestoreMatchStatus'

const WebSocketContext = createContext<WebSocket | null>(null)

export const WebSocketProvider = ({ children }: { children: React.ReactNode }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const maxReconnectAttempts = 5

  const userId = useMatchStatusStore((state) => state.userId)

  const connectWebSocket = () => {
    if (reconnectAttempts >= maxReconnectAttempts) {
      console.error('⚠️ 再接続の最大回数に達しました。接続を停止します。')
      return
    }

    const ws = new WebSocket(`ws://localhost:8000/ws?user_id=${userId}`)
    setSocket(ws)

    ws.onopen = () => {
      console.log('✅ WebSocket 接続完了')
      setReconnectAttempts(0)
    const restore = async () => {
      await useRestoreMatchStatus(userId)
    }
    restore()
    }

    ws.onclose = () => {
      console.log('❌ WebSocket 接続終了。再接続を試みます...')
      setReconnectAttempts((prev) => prev + 1)
      setTimeout(() => {
        connectWebSocket()
      }, 3000)
    }

    ws.onerror = (err) => {
      console.error('⚠️ WebSocket エラー:', err)
    }

    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocketメッセージ受信:', data)

      if (data.type === 'status_update') {
        await useRestoreMatchStatus(userId)
      }
    }

    return ws
  }

  useEffect(() => {
    const ws = connectWebSocket()
    return () => {
      ws?.close()
    }
  }, [userId])

  return (
    <WebSocketContext.Provider value={socket}>
      {children}
    </WebSocketContext.Provider>
  )
}

export const useSocket = () => useContext(WebSocketContext)



