# services/ConnectionManager.py
from fastapi import WebSocket
from typing import Dict
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections[user_id] = websocket
            print(f"✅ User {user_id} connected.")

    async def disconnect(self, user_id: int):
        async with self.lock:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
                print(f"❌ User {user_id} disconnected.")

    async def send_to_text_user(self, user_id: int, message: str):
        async with self.lock:
            ws = self.active_connections.get(user_id)
            if ws:
                await ws.send_text(message)
    
    async def send_to_json_user(self, user_id: int, message: dict):
        async with self.lock:
            print(f"user_id: {user_id}")
            print(f"active_connections: {self.active_connections}")
            ws = self.active_connections.get(user_id)
            print(f"Sending message to user {ws}: {message}")
            if ws:
                await ws.send_json(message)

    async def broadcast(self, message: str):
        async with self.lock:
            for ws in self.active_connections.values():
                await ws.send_text(message)
