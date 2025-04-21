// src/contexts/WebSocketContext.tsx
import { createContext, useContext, useEffect, useState } from 'react';

const WebSocketContext = createContext<WebSocket | null>(null);

export const WebSocketProvider = ({ children }: { children: React.ReactNode }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0); // 再接続試行回数を管理
  const maxReconnectAttempts = 5; // 再接続の最大回数

  const connectWebSocket = () => {
    if (reconnectAttempts >= maxReconnectAttempts) {
      console.error('⚠️ 再接続の最大回数に達しました。接続を停止します。');
      return;
    }

    const ws = new WebSocket('ws://localhost:8000/ws?user_id=2'); // 動的なユーザーIDも対応可能
    setSocket(ws);

    ws.onopen = () => {
      console.log('✅ WebSocket 接続完了');
      setReconnectAttempts(0); // 接続成功時に試行回数をリセット
    };

    ws.onclose = () => {
      console.log('❌ WebSocket 接続終了。再接続を試みます...');
      setReconnectAttempts((prev) => prev + 1); // 試行回数を増加
      setTimeout(() => {
        connectWebSocket(); // 再接続を試みる
      }, 3000); // 3秒後に再接続
    };

    ws.onerror = (err) => {
      console.error('⚠️ WebSocket エラー:', err);
    };

    return ws;
  };

  useEffect(() => {
    const ws = connectWebSocket();

    return () => {
      ws.close();
    };
  }, []);

  return (
    <WebSocketContext.Provider value={socket}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useSocket = () => useContext(WebSocketContext);

