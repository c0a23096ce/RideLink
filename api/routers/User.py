from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session

from api.services.UserService import UserService
from api.schemas.users import UserCreate, User, UserLogin, Token, TokenData
from api.dependencies import get_db, get_token_data, get_current_user

router = APIRouter()

@router.post("/register", response_model=User)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    新規ユーザー登録エンドポイント
    """
    user_service = UserService(db)
    user = user_service.register_user(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        password=user_data.password
    )
    
    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    return user

@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin, 
    db: Session = Depends(get_db)
):
    """
    ログインエンドポイント
    """
    user_service = UserService(db)
    user = user_service.authenticate_user(
        user_data.email, 
        user_data.password
    )
    
    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )
    
    access_token = user_service.create_access_token(data={"sub": user.email}) # emailをトークンに含める
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    トークンから現在のユーザー情報を取得するエンドポイント
    """
    return current_user
