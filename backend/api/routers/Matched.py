from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies import get_db , get_connection_manager
import schemas.routes as route_schema
from services.MatchedService import MatchedService
from fastapi.responses import HTMLResponse
from typing import Dict
from config import settings
from services.Enums import UserStatus
from services.ConnectionManager import ConnectionManager
import schemas.routes as route_schema

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

@router.post("/{match_id}/complete")
async def report_completion(match_id: int, user_data: route_schema.ComplateUser, db: Session = Depends(get_db), connection_manager: ConnectionManager = Depends(get_connection_manager)):
    """目的地に到達したことを報告するエンドポイント

    Args:
        match_id (int): マッチID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).
    
    Returns:
        dict: 成功可否
    """
    matching_service = MatchedService(db, connection_manager)
    res = await matching_service.report_ride_completion(match_id=match_id, user_id=user_data.user_id)
    return res

@router.patch("/{match_id}/review-targets/{user_id}")
async def evaluate_match(evaluation_data: route_schema.ReviewRequest, db: Session = Depends(get_db), connection_manager: ConnectionManager = Depends(get_connection_manager)):
    """マッチング相手の評価を行う終了エンドポイント

    Args:
        match_id (int): マッチID
        user_id (int): ユーザーID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).
        evaluation_data: ユーザーIDをキーに持ち、評価値をValueに持つ辞書
    
    Returns:
        dict: 成功可否
    """
    matching_service = MatchedService(db, connection_manager)
    return await matching_service.update_evaluation(
        match_id=evaluation_data.match_id,
        user_id=evaluation_data.user_id,
        ratings=evaluation_data.ratings
        )

@router.get("/{user_id}")
async def get_match_id(user_id: int, db: Session = Depends(get_db), connection_manager: ConnectionManager = Depends(get_connection_manager)):
    """ユーザーのマッチIDを取得するエンドポイント

    Args:
        user_id (int): ユーザーID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        dict: マッチID
    """
    # マッチングサービスのインスタンスを作成
    matching_service = MatchedService(db, connection_manager)
    # マッチIDを取得
    match_id = await matching_service.get_match_id(user_id)

    if not match_id:
        return {"error": "マッチが見つかりません"}
    
    return {"match_id": match_id}

@router.get("/{user_id}/status")
async def get_user_status(user_id: int, db: Session = Depends(get_db), connection_manager: ConnectionManager = Depends(get_connection_manager)):
    """ユーザーのマッチング状況を取得するエンドポイント

    Args:
        user_id (int): ユーザーID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        dict: マッチング状況
    """
    # マッチングサービスのインスタンスを作成
    matching_service = MatchedService(db, connection_manager)
    # マッチング状況を取得
    status = await matching_service.get_user_status(user_id)

    if not status:
        return {"status": UserStatus.IDOL}
    
    return {"status": status}

@router.get("/{match_id}/review-targets/{user_id}")
async def get_review_targets(
    match_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    connection_manager: ConnectionManager = Depends(get_connection_manager)
):
    matching_service = MatchedService(db, connection_manager)
    review_target = await matching_service.get_reviwew_target(match_id, user_id)
    if not review_target:
        return {"error": "評価対象のユーザーが見つかりません"}
    return review_target

@router.get("/{match_id}/route") # , response_model=route_schema.RouteResponse
async def get_route(match_id: int, db: Session = Depends(get_db), connection_manager: ConnectionManager = Depends(get_connection_manager)):
    """決定したマッチのルート情報とユーザーの位置を取得する

    Args:
        match_id : マッチID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        ApprovePassengerResponse: 承認の結果
        処理成功 or 失敗(bool)、メッセージ、ステータスメッセージ
    """
    # マッチングサービスのインスタンスを作成
    matching_service = MatchedService(db, connection_manager)
    # ルート情報を取得
    route = await matching_service.get_matched_route(match_id)

    if not route:
        return {"error": "ルート情報が見つかりません"}
    
    users = await matching_service.get_users_by_match(match_id)
    
    
    users_list = []
    for user in users:
        users_list.append({
            "user_id": user.user_id,
            "start": [user.user_start_lat, user.user_start_lng],
            "destination": [user.user_destination_lat, user.user_destination_lng],
            "role": user.user_role,
        })
    
    return {"route": route, "users": users_list}

