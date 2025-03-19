from pydantic import BaseModel, Field
from typing import Tuple, List

class User(BaseModel):
    id: int = Field(..., example=1)
    current_location: Tuple[float, float] = Field(..., example=(35.681236, 139.767125))
    destination: Tuple[float, float] = Field(..., example=(35.681236, 139.767125))

class Match(BaseModel):
    matched_users: List[Tuple[User, User]]