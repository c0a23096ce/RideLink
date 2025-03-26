from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from api.dependencies import get_db
from api.services.MatchingService import MatchingService

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/match/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: int, db: Session = Depends(get_db)):
    matching_service = MatchingService(db)
    await websocket.accept()
    
    # WebSocket接続を登録
    await matching_service.register_connection(player_id, websocket)
    
    try:
        while True:
            # WebSocketからのメッセージ待機
            data = await websocket.receive_json() # メッセージが受信されるまで待機
            # メッセージの種類に応じた処理
            if data.get("type") == "join_pool":
                await matching_service.add_player_to_pool(
                    player_id=player_id,
                    skill_level=data.get("skill_level", 1000),
                    preferences=data.get("preferences", {}),
                    location=data.get("location")
                )
            elif data.get("type") == "confirm_match":
                match_id = data.get("match_id")
                if match_id:
                    await matching_service.confirm_match(match_id, player_id)
    except WebSocketDisconnect:
        print(f"Client #{player_id} disconnected")
    finally:
        # 接続解除処理
        await matching_service.unregister_connection(player_id)