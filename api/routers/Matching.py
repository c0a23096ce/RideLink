from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.dependencies import get_db
from api.services.MatchingService import MatchingService
import api.schemas.matchs as match_shema

router = APIRouter()

# ロビー作成エンドポイント
@router.post("/matching/create_lobby", response_model=match_shema.CreateLobbyResponse)
async def create_lobby(match_data: match_shema.MatchCreate, db: Session = Depends(get_db)):
    matching_service = MatchingService(db)
    lobby = await matching_service.create_driver_lobby(
        driver_id=match_data.driver_id,
        starting_location=match_data.driver_location,
        destination=match_data.destination,
    )
    return lobby

# ロビー参加エンドポイント
@router.post("/matching/join_lobby", response_model=match_shema.JoinLobbyResponse)
async def join_lobby(match_data: match_shema.MatchJoin, db: Session = Depends(get_db)):
    matching_service = MatchingService(db)
    result = await matching_service.request_random_ride(
        passenger_id=match_data.passenger_id, 
        passenger_location=match_data.passenger_location,
        passenger_destination=match_data.passenger_destination
        )
    return result

# ドライバー承認エンドポイント
@router.post("/matching/approve_passenger", response_model=match_shema.ApprovePassengerResponse)
async def driver_approve_passenger(approve_data: match_shema.ApproveDriverMatch, db: Session = Depends(get_db)):
    matching_service = MatchingService(db)
    result = await matching_service.driver_approve_passenger(
        driver_id=approve_data.driver_id, 
        lobby_id=approve_data.lobby_id, 
        passenger_id=approve_data.passenger_id
        )
    return result

# 乗車者承認エンドポイント
@router.post("/matching/approve_driver", response_model=match_shema.ApprovePassengerResponse)
async def passenger_approve_driver(approve_data: match_shema.ApprovePassengerMatch, db: Session = Depends(get_db)):
    matching_service = MatchingService(db)
    result = await matching_service.passenger_approve_ride(
        passenger_id=approve_data.passenger_id, 
        lobby_id=approve_data.lobby_id
        )
    return result

# ロビー一覧取得エンドポイント
@router.get("/matching/get_all_lobby")
async def get_all_lobby(db: Session = Depends(get_db)):
    matching_service = MatchingService(db)
    result = await matching_service.get_all_lobbies()
    return result

@router.get("/matching/get_lobby/{lobby_id}")
async def get_lobby_info(lobby_id: str, db: Session = Depends(get_db)):
    matching_service = MatchingService(db)
    result = await matching_service.get_lobby_info(lobby_id)
    return result
