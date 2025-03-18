from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class User(UserBase):
    user_id: int

    class Config:
        orm_mode = True
        from_attributes = True  # Pydantic v2での属性変換設定

# ログイン用のスキーマを追加
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# トークン応答用のスキーマ
class Token(BaseModel):
    access_token: str
    token_type: str

# トークンのペイロード用のスキーマ
class TokenData(BaseModel):
    email: str | None = None