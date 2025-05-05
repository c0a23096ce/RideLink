// src/contexts/WebSocketContext.tsx
import { createContext, useContext, useEffect, useState } from 'react'
import { useMatchStatusStore } from '../store/matchStatusStore'
import apiClient from '../lib/apiClient'

const WebSocketContext = createContext<WebSocket | null>(null)

export const WebSocketProvider = ({ children }: { children: React.ReactNode }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const maxReconnectAttempts = 5

  const setStatus = useMatchStatusStore((s) => s.setStatus)
  const userId = 2 // 動的ユーザーIDに後で変えるのもOK

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

    // ✅ onmessageを一元管理
    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocketメッセージ受信:', data)

      if (data.type === 'status_update') {
        try {
          // 🔥 マッチID問い合わせAPI
          const userId = useMatchStatusStore.getState().userId
          const res_1 = await apiClient.get(`/matches/${userId}`)
          const matchId = res_1.data.match_id
          console.log('現在のマッチID:', matchId)
          
          if (!matchId) {
            console.warn('マッチIDが見つかりません')
            setStatus(null)
            return
          }

          // 🔥 ステータス問い合わせAPI
          const res_2 = await apiClient.get(`/matches/${userId}/status`)
          const currentStatus = res_2.data.status
          console.log('取得したステータス:', currentStatus)

          // 🔥 Zustandを更新 ('approved:123' 形式)
          setStatus(`${currentStatus}:${matchId}`)
        } catch (error) {
          console.error('ステータス問い合わせに失敗:', error)
          setStatus(null)
        }
      }
    }

    return ws
  }

  useEffect(() => {
    const setUserId = useMatchStatusStore.getState().setUserId
    setUserId(2) // テスト用のユーザーIDを設定
    const ws = connectWebSocket()
    return () => {
      ws?.close()
    }
  }, [])

  return (
    <WebSocketContext.Provider value={socket}>
      {children}
    </WebSocketContext.Provider>
  )
}

export const useSocket = () => useContext(WebSocketContext)


