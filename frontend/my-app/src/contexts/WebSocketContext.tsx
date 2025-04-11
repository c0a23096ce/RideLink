// src/contexts/WebSocketContext.tsx
'use client';

import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  ReactNode,
} from 'react';

const WebSocketContext = createContext<WebSocket | null>(null);

export const WebSocketProvider = ({ children }: { children: ReactNode }) => {
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    socketRef.current = new WebSocket('ws://localhost:8000/ws?user_id=2');

    socketRef.current.onopen = () => {
      console.log('[WebSocket] 接続成功');
      setConnected(true);
    };

    socketRef.current.onclose = () => {
      console.log('[WebSocket] 切断されました');
      setConnected(false);
    };

    return () => {
      socketRef.current?.close();
    };
  }, []);

  return (
    <WebSocketContext.Provider value={socketRef.current}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useSocket = () => useContext(WebSocketContext);