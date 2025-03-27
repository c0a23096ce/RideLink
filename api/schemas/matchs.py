from pydantic import BaseModel, Field
from typing import Tuple, List, Dict, Any

class User(BaseModel):
    id: int = Field(..., example=1)
    current_location: Tuple[float, float] = Field(..., example=(35.681236, 139.767125))
    destination: Tuple[float, float] = Field(..., example=(35.681236, 139.767125))

class Match(BaseModel):
    matched_users: List[Tuple[User, User]]

class MatchCreate(BaseModel):
    driver_id: int = Field(..., example=1)
    driver_location: Tuple[float, float] = Field(..., example=(35.681236, 139.767125))
    destination: Tuple[float, float] = Field(..., example=(35.681236, 139.767125))

class MatchJoin(BaseModel):
    passenger_id: int = Field(..., example=1)
    passenger_location: Tuple[float, float] = Field(..., example=(35.681236, 139.767125))
    destination: Tuple[float, float] = Field(..., example=(35.681236, 139.767125))

class CreateLobbyResponse(BaseModel):
    success: bool = Field(..., example=True)  # 成功フラグ
    lobby_id: str = Field(..., example="123e4567-e89b-12d3-a456-426614174000")  # ロビーID
    lobby: Dict[str, Any] = Field(..., example={
        "lobby_id": "123e4567-e89b-12d3-a456-426614174000",
        "driver_id": 1,
        "starting_location": (35.681236, 139.767125),
        "destination": (35.689487, 139.691706),
        "max_distance": 5.0,
        "max_passengers": 4,
        "current_passengers": 0,
        "status": "open",
        "created_at": 1672531200.0,
        "preferences": {}
    })  # ロビー情報