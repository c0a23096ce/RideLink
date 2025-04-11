from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.services.MatchingService import MatchingService

# APIRouterを作成
router = APIRouter()

# MatchingServiceのインスタンスを取得
matching_service = MatchingService()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    # WebSocket接続を受け入れる
    await websocket.accept()
    
    # MatchingServiceに接続を登録
    await matching_service.register_connection(user_id, websocket)
    
    try:
        while True:
            # クライアントからのメッセージを受信
            data = await websocket.receive_text()
            await websocket.send_text(f"受信しました: {data}")
            print(f"Received from {user_id}: {data}")
    except WebSocketDisconnect:
        # クライアントが切断した場合、MatchingServiceから接続を解除
        await matching_service.unregister_connection(user_id)
        print(f"User {user_id} disconnected")