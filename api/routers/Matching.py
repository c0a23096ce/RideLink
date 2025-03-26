from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.dependencies import get_db
from api.services.MatchingService import MatchingService
import api.schemas.matchs as match_shema

router = APIRouter()

@router.post("/pool/join")
async def join_pool(player_id: int, skill_level: int, db: Session = Depends(get_db)):
    matching_service = MatchingService(db)
    entry = await matching_service.add_player_to_pool(
        player_id=player_id,
        skill_level=skill_level,
        preferences={},
        location=None
    )
    return {"message": "Player added", "entry": {
        "player_id": entry.player_id,
        "status": entry.status
    }}