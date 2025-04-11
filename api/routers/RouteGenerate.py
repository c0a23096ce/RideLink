from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.dependencies import get_db
from api.services.MatchingService import MatchingService
from api.services.RouteGenerateService import RouteGenerateService
import api.schemas.routes as route_schema
from fastapi.responses import HTMLResponse
from api.config import settings

router = APIRouter(
    prefix="/route",
    tags=["Route"],
    responses={404: {"description": "Not found"}},
)

@router.post("/generate")
async def create_route(request_data):
    """
    乗客のpickup→dropoff制約を守った最適ルートをGeoJSONで返す
    """
    route_service = RouteGenerateService(
        api_key=settings.mapbox_api_key,
        coordinates=request_data.coordinates,
        pickups_deliveries=request_data.pickups_deliveries,
        start_index=request_data.start_index,
        end_index=request_data.end_index
    )

    geojson = await route_service.get_geojson_route()

    if not geojson:
        return {"error": "ルートの最適化に失敗しました"}

    return {"route": geojson}
