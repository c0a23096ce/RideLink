from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.dependencies import get_db
from api.services.MatchingService import MatchingService
import api.schemas.matchs as match_shema

router = APIRouter()

@router.post("/matching/create_lobby", response_model=match_shema.CreateLobbyResponse)
async def create_lobby(match_data: match_shema.MatchCreate, db: Session = Depends(get_db)):
    matching_service = MatchingService(db)
    lobby = matching_service.create_driver_lobby(
        driver_id=match_data.driver_id,
        location=match_data.starting_location,
        destination=match_data.destination,
    )
    return lobby

@router.post("/matching/join_lobby")
async def join_lobby(match_data: match_shema.MatchJoin, db: Session = Depends(get_db)):
    matching_service = MatchingService(db)
    matching_service.request_random_ride(match_data.user_id)
