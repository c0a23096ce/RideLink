from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies import get_db
import schemas.routes as route_schema
from services.MatchedService import MatchedService
from fastapi.responses import HTMLResponse
from config import settings
from services.Enums import UserStatus

router = APIRouter(
    prefix="/matches",
    tags=["Matches"],
    responses={404: {"description": "Not found"}},
)

@router.post("/generate")
async def create_route(request_data):
    """ルート生成エンドポイント
    Args:
        request_data (dict): リクエストデータ
    Returns:
        dict: レスポンスデータ
    """
    pass

@router.get("/{user_id}")
async def get_match_id(user_id: int, db: Session = Depends(get_db)):
    """ユーザーのマッチIDを取得するエンドポイント

    Args:
        user_id (int): ユーザーID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        dict: マッチID
    """
    # マッチングサービスのインスタンスを作成
    matching_service = MatchedService(db)
    # マッチIDを取得
    match_id = await matching_service.get_match_id(user_id)

    if not match_id:
        return {"error": "マッチが見つかりません"}
    
    return {"match_id": match_id}

@router.get("/{user_id}/status")
async def get_user_status(user_id: int, db: Session = Depends(get_db)):
    """ユーザーのマッチング状況を取得するエンドポイント

    Args:
        user_id (int): ユーザーID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        dict: マッチング状況
    """
    # マッチングサービスのインスタンスを作成
    matching_service = MatchedService(db)
    # マッチング状況を取得
    status = await matching_service.get_user_status(user_id)

    if not status:
        return {"status": UserStatus.IDOL}
    
    return {"status": status}

@router.get("/{match_id}/route") # , response_model=route_schema.RouteResponse
async def get_route(match_id: int, db: Session = Depends(get_db)):
    """決定したマッチのルート情報を取得する

    Args:
        match_id : マッチID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        ApprovePassengerResponse: 承認の結果
        処理成功 or 失敗(bool)、メッセージ、ステータスメッセージ
    """
    # マッチングサービスのインスタンスを作成
    matching_service = MatchedService(db)
    # ルート情報を取得
    route = await matching_service.get_matched_route(match_id)

    if not route:
        return {"error": "ルート情報が見つかりません"}
    
    return {"route": route}

