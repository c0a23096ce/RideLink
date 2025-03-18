from pydantic import BaseModel, Field
from typing import Tuple, List

class User(BaseModel):
    id: int
    current_location: Tuple[float, float]
    destination: Tuple[float, float]

class Match(BaseModel):
    matched_users: List[Tuple[User, User]]