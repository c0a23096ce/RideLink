from pydantic import BaseModel, Field
from typing import Tuple, List, Dict, Any, Optional

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
    passenger_id: int = Field(..., example=2)
    passenger_location: Tuple[float, float] = Field(..., example=(35.681236, 139.767125))
    passenger_destination: Tuple[float, float] = Field(..., example=(35.681236, 139.767125))

class ApproveLobby(BaseModel):
    user_id: int = Field(..., example=1)
    lobby_id: str = Field(..., example="123e4567-e89b-12d3-a456-426614174000")
    

class CreateLobbyResponse(BaseModel):
    success: bool
    lobby_id: str = None  # Noneを許可する
    lobby: dict = None    # Noneを許可する
    error: str = None     # エラーメッセージ用フィールド
    
class JoinLobbyResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    lobby: Optional[Dict[str, Any]] = None
    start_distance: Optional[float] = None
    destination_distance: Optional[float] = None

class ApprovePassengerResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    confirmed: Optional[str] = None