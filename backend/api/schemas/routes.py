from pydantic import BaseModel, Field, conint, validator, model_validator
from typing import Tuple, List, Dict, Any, TypeAlias
class ComplateUser(BaseModel):
    user_id: int = Field(..., description="ユーザーID")

# class ReviewTarget(BaseModel):
#     match_id: int = Field(..., description="マッチID")
#     user_id: int = Field(..., description="ユーザーID")

class ReviewRequest(BaseModel):
    match_id: int
    user_id: int
    ratings: Dict[int, int]

    @validator("ratings")
    def validate_rating_values(cls, v):
        for k, value in v.items():
            if not (1 <= value <= 5):
                raise ValueError("評価スコアは1から5の間でなければなりません")
        return v

    @validator("ratings")
    def no_empty_ratings(cls, v):
        if not v:
            raise ValueError("少なくとも1人は評価してください")
        return v

    @model_validator(mode='after')
    def check_something(self) -> 'ReviewRequest':
        # self.ratings や self.user_id にアクセス可
        if self.user_id in self.ratings:
            raise ValueError("自分自身を評価することはできません")
        return self