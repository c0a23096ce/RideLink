from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session

from services.UserService import UserService
from schemas.users import UserCreate, User, UserLogin, Token, TokenData
from dependencies import get_db, get_token_data, get_current_user

from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/user",
    tags=["User"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_model=User)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """ユーザー登録エンドポイント

    Args:
        user_data (UserCreate): 名前、メールアドレス、電話番号、パスワード
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        User: 名前、メールアドレス、電話番号、ユーザーID
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

# @router.post("/login", response_model=Token)
# async def login(
#     user_data: UserLogin, 
#     db: Session = Depends(get_db)
# ):
#     """ユーザーログインエンドポイント
#     Args:
#         user_data (UserLogin): メールアドレス、パスワード
#         db (Session, optional): データベースセッション. Defaults to Depends(get_db).
#     Returns:
#         Token: アクセストークン、トークンタイプ
#     """
#     user_service = UserService(db)
#     user = user_service.authenticate_user(
#         user_data.email, 
#         user_data.password
#     )
    
#     if user is None:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid credentials"
#         )
    
#     access_token = user_service.create_access_token(data={"sub": user.email}) # emailをトークンに含める
#     return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """FastAPIのOAuth2PasswordRequestFormを使用したログインエンドポイント

    Args:
        form_data (OAuth2PasswordRequestForm, optional): メールアドレス、パスワード
        db (Session, optional): データベースセッション. Defaults to Depends(get_db).

    Returns:
        Token: アクセストークン、トークンタイプ 
    """
    
    print(f"Received username: {form_data.username}")
    print(f"Received password: {form_data.password}")
    
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = user_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """トークンから現在のユーザー情報を取得するエンドポイント
    Args:
        current_user (User, optional): 現在のユーザー. Defaults to Depends(get_current_user).
    Returns:
        User: 現在のユーザー情報
    """
    return current_user
