from fastapi import APIRouter
from api.services.matching import MatchingService
import api.schemas.matchs as match_shema

router = APIRouter()
matching_service = MatchingService(max_distance_km=5)


# あとでマッチングしてるUserの組を取得するように変更
@router.get("/matching", response_model=match_shema.Match)
async def matching(users: list[match_shema.User]):
    matches = matching_service.find_matches(users)
    return match_shema.Match(matched_users=matches)

# User型のリストを受け取ってマッチングしたユーザーの組をタプルにしてリストで返す
@router.post("/matching", response_model=match_shema.Match)
async def matching_post(users: list[match_shema.User]):
    matches = matching_service.find_matches(users)
    return match_shema.Match(matched_users=matches)