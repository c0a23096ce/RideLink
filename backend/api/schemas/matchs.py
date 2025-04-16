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
    destination: Tuple[float, float] = Field(..., example=(35.671667, 139.763056))

class MatchJoin(BaseModel):
    passenger_id: int = Field(..., example=2)
    passenger_location: Tuple[float, float] = Field(..., example=(35.684295, 139.774124))
    passenger_destination: Tuple[float, float] = Field(..., example=(35.666247, 139.758093))

class ApproveLobby(BaseModel):
    user_id: int = Field(..., example=1)
    

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