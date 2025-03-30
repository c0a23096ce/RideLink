from pydantic import BaseModel, Field
from typing import Tuple, List, Dict, Any

class RouteGenerateRequest(BaseModel):
    driver_location: Tuple[float, float] = Field(..., example=(35.6667, 139.3300), description="ドライバーの現在位置 (緯度, 経度)")
    passenger_location: Tuple[float, float] = Field(..., example=(35.6700, 139.3400), description="乗客の現在位置 (緯度, 経度)")
    driver_destination: Tuple[float, float] = Field(..., example=(35.6800, 139.3500), description="ドライバーの目的地 (緯度, 経度)")
    passenger_destination: Tuple[float, float] = Field(..., example=(35.6900, 139.3600), description="乗客の目的地 (緯度, 経度)")

class RouteGenerateResponse(BaseModel):
    segments: List[Dict[str, Any]]
    total_distance: float
    total_duration: float
    route_order: List[str]