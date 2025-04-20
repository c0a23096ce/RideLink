from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
from services.ConnectionManager import ConnectionManager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # WebSocketオブジェクトからアプリケーションの状態にアクセス
    user_id = websocket.query_params.get("user_id")
    if not user_id:
        await websocket.close(code=1008)  # 必須パラメータがない場合は接続を閉じる
        return

    try:
        user_id = int(user_id)  # strからintに変換
    except ValueError:
        await websocket.close(code=1008)  # 不正なパラメータの場合は接続を閉じる
        return

    connection_manager: ConnectionManager = websocket.app.state.connection_manager
    await connection_manager.connect(user_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await connection_manager.disconnect(user_id)



