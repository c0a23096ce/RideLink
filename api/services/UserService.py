from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from api.models.models import User
from api.cruds.UserCRUD import UserCRUD

from dotenv import load_dotenv
import os

load_dotenv()

# JWT設定
SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # セキュリティ上、環境変数などで管理してください
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

class UserService:
    def __init__(self, db_session: Session):
        # データベースセッションを初期化
        self.db_session = db_session
        # パスワードハッシュ化用のコンテキスト
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # UserCRUDインスタンスを作成
        self.user_crud = UserCRUD(db_session)
    
    def register_user(self, name: str, email: str, phone: str, password: str) -> Optional[User]:
        """
        新規ユーザーを登録します
        
        Args:
            name: ユーザー名
            email: メールアドレス
            phone: 電話番号
            password: パスワード（平文）
            
        Returns:
            作成されたユーザーオブジェクト、またはNone（エラー時）
        """
        try:
            # パスワードをハッシュ化
            hashed_password = self.pwd_context.hash(password)
            
            # ユーザー情報をデータベースに保存
            user_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "hashed_password": hashed_password
            }
            
            # CRUDを使用してユーザーを作成
            return self.user_crud.create_user(user_data)
            
        except IntegrityError:
            # メールアドレスの重複などでエラーが発生した場合
            self.db_session.rollback()
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        ユーザーを認証します
        
        Args:
            email: メールアドレス
            password: パスワード（平文）
            
        Returns:
            認証されたユーザーオブジェクト、または認証失敗時はNone
        """
        # メールアドレスでユーザーを取得
        user = self.user_crud.get_user_by_email(email)
        
        if not user:
            return None
            
        # パスワード検証
        if not self.pwd_context.verify(password, user.hashed_password):
            return None
            
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        アクセストークンを生成します
        
        Args:
            data: トークンに含めるデータ
            expires_delta: トークンの有効期限
            
        Returns:
            生成されたJWTトークン
        """
        to_encode = data.copy() # データをコピー
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)) # 有効期限を計算
        to_encode.update({"exp": expire}) # 有効期限を追加
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        emailから現在のユーザーを取得します
        
        Args:
            token: JWTトークン
            
        Returns:
            emailに対応するユーザーオブジェクト、またはNone（エラー時）
        """
        user = self.user_crud.get_user_by_email(email)
        if user is None:
            print("No user found in UserService")
        else:
            print(f"User found in UserService: {user}")
        return user