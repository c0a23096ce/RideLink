from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.schemas.users import TokenData
from api.services.UserService import UserService
from api.schemas.users import User as UserSchema

from dotenv import load_dotenv
import os

load_dotenv()
# JWT設定
SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # セキュリティ上、環境変数などで管理してください
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")


# OAuth2のトークンURLを設定
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/testlogin")

def get_db() -> Generator:
    """
    リクエストごとにデータベースセッションを提供する依存性関数
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_token_data(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    トークンからトークンデータを抽出する
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # トークンからペイロードを取得
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
        # TokenDataオブジェクトを作成して返す
        return TokenData(email=email)
    except JWTError:
        raise credentials_exception

def get_current_user(token_data: TokenData = Depends(get_token_data), db: Session = Depends(get_db)): # 複数回使用するためトークンデータからユーザーを取得する依存性関数を作成
    """
    トークンデータを抽出し、トークンデータのemailから現在のユーザーを取得する
    """
    print(f"トークンデータのemail: {token_data.email}")
    user_service = UserService(db)
    print(f"ユーザーサービス: {user_service}")
    user = user_service.get_user_by_email(token_data.email)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    # SQLAlchemyオブジェクトはそのままでは返せないのでPydanticモデルに変換
    return UserSchema.from_orm(user)