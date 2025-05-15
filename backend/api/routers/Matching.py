from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from dependencies import get_db, get_matching_service
import schemas.matchs as match_shema
from services.MatchingService import MatchingService

router = APIRouter(
    prefix="/matching",
    tags=["Matching"],
    responses={404: {"description": "Not found"}}
)

# ロビーの作成API
@router.post("/lobbies", response_model=match_shema.CreateLobbyResponse)
async def create_lobby(
    match_data: match_shema.MatchCreate,
    db: Session = Depends(get_db),
    matching_service: MatchingService = Depends(get_matching_service)
):
    matching_service.set_db(db)
    return await matching_service.create_driver_lobby(
        driver_id=match_data.driver_id,
        starting_location=match_data.driver_location,
        destination=match_data.destination,
    )

# ロビーの取得API
@router.get("/lobbies")
async def get_all_lobby(
    db: Session = Depends(get_db),
    matching_service: MatchingService = Depends(get_matching_service)
):
    matching_service.set_db(db)
    return await matching_service.get_all_lobbies()

# ロビーの詳細情報取得API
@router.get("/lobbies/{lobby_id}")
async def get_lobby_info(
    lobby_id: str,
    db: Session = Depends(get_db),
    matching_service: MatchingService = Depends(get_matching_service)
):
    matching_service.set_db(db)
    return await matching_service.get_lobby_info(lobby_id)

# ロビーのユーザー情報取得API
@router.get("/lobbies/{lobby_id}/users")
async def get_lobby_users(
    lobby_id: int,
    db: Session = Depends(get_db),
    matching_service: MatchingService = Depends(get_matching_service)
):
    matching_service.set_db(db)
    return await matching_service.get_lobby_users(lobby_id)

# ロビーの参加API
@router.post("/join_lobby", response_model=match_shema.JoinLobbyResponse)
async def join_lobby(
    match_data: match_shema.MatchJoin,
    db: Session = Depends(get_db),
    matching_service: MatchingService = Depends(get_matching_service)
):
    matching_service.set_db(db)
    return await matching_service.request_random_ride(
        passenger_id=match_data.passenger_id,
        passenger_location=match_data.passenger_location,
        passenger_destination=match_data.passenger_destination
    )

# ロビーの承認API
@router.post("/lobbies/{lobby_id}/approved")
async def lobby_approve(
    lobby_id: int,
    approve_data: match_shema.ApproveLobby,
    db: Session = Depends(get_db),
    matching_service: MatchingService = Depends(get_matching_service)
):
    matching_service.set_db(db)
    return await matching_service.approve_ride(
        user_id=approve_data.user_id,
        lobby_id=lobby_id
    )

# ロビーの拒否API
@router.patch("/lobbies/{match_id}/cancel")
async def cancel_lobby(
    match_data: match_shema.CancelLobby,
    db: Session = Depends(get_db),
    matching_service: MatchingService = Depends(get_matching_service)
):
    matching_service.set_db(db)
    return await matching_service.cancel_ride_request(
        passenger_id=match_data.user_id,
        lobby_id=match_data.match_id
    )
