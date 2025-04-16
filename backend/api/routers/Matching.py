from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies import get_db
from services.MatchingService import MatchingService
import schemas.matchs as match_shema

router = APIRouter(
    prefix="/matching",
    tags=["Matching"],
    responses={404: {"description": "Not found"}},
)

@router.post("/lobbies", response_model=match_shema.CreateLobbyResponse)
async def create_lobby(match_data: match_shema.MatchCreate, db: Session = Depends(get_db)):
    """ドライバーのロビー作成エンドポイント
    
    Args:
        match_data (match_shema.MatchCreate): ドライバーID、ドライバーの位置情報、目的地
        db (Session, optional): データベースセッション. Defaults to Depends(get_db)
    
    Returns:
        CreateLobbyResponse: ロビー作成の結果
        処理成功 or 失敗(bool)、ロビーID(str)、ロビー情報(dict)、エラーメッセージ(str)
    """
    matching_service = MatchingService(db)
    lobby = await matching_service.create_driver_lobby(
        driver_id=match_data.driver_id,
        starting_location=match_data.driver_location,
        destination=match_data.destination,
    )
    print(lobby)
    return lobby

@router.get("/lobbies")
async def get_all_lobby(db: Session = Depends(get_db)):
    """ロビー一覧取得エンドポイント

    Args:
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        dict: ロビー情報のリスト
    """
    matching_service = MatchingService(db)
    result = await matching_service.get_all_lobbies()
    return result

@router.get("/lobbies/{lobby_id}")
async def get_lobby_info(lobby_id: str, db: Session = Depends(get_db)):
    """ロビー情報取得エンドポイント

    Args:
        lobby_id (str): ロビーID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        dict: ロビー情報
    """
    matching_service = MatchingService(db)
    result = await matching_service.get_lobby_info(lobby_id)
    return result

@router.get("/lobbies/{lobby_id}/users")
async def get_lobby_users(lobby_id: str, db: Session = Depends(get_db)):
    """ロビー参加者情報取得エンドポイント

    Args:
        lobby_id (str): ロビーID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        dict: ロビー参加者情報
    """
    matching_service = MatchingService(db)
    result = await matching_service.get_lobby_users(lobby_id)
    return result

@router.post("/join_lobby", response_model=match_shema.JoinLobbyResponse)
async def join_lobby(match_data: match_shema.MatchJoin, db: Session = Depends(get_db)):
    """作成されたロビーに参加するエンドポイント

    Args:
        match_data (match_shema.MatchJoin): 乗客ID、乗客の位置情報、目的地
        db (Session, optional): データベースセッション. Defaults to Depends(get_db)

    Returns:
        JoinLobbyResponse: ロビー参加の結果
        処理成功 or 失敗(bool)、メッセージ、エラーメッセージ、ロビー情報、出発地までの距離、目的地までの距離
    """
    matching_service = MatchingService(db)
    result = await matching_service.request_random_ride(
        passenger_id=match_data.passenger_id, 
        passenger_location=match_data.passenger_location,
        passenger_destination=match_data.passenger_destination
        )
    print(result)
    return result

@router.post("/lobbies/{lobby_id}/approved")
async def lobby_approve(lobby_id: str, approve_data: match_shema.ApproveLobby, db: Session = Depends(get_db)):
    """ロビーを承認するエンドポイント

    Args:
        approve_data (match_shema.ApproveDriverMatch): ユーザーID、ロビーID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        ApprovePassengerResponse: 承認の結果
        処理成功 or 失敗(bool)、メッセージ、ステータスメッセージ
    """
    matching_service = MatchingService(db)
    result = await matching_service.approve_ride(
        user_id=approve_data.user_id,
        lobby_id=lobby_id
    )
    return result

@router.patch("lobbies/{match_id}/complete")
async def complete_ride(match_id: int, db: Session = Depends(get_db)):
    """乗車完了エンドポイント
    
    Args:
        match_id (int): マッチングID
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).
    
    Returns:
        dict: 処理結果
    """
    matching_service = MatchingService(db)
    result = await matching_service.report_ride_completion(match_id)
    return result