from pydantic import BaseModel, Field
from typing import Tuple, List, Dict, Any

class ComplateUser(BaseModel):
    user_id: int = Field(..., description="ユーザーID")