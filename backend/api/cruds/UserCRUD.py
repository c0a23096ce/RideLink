from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Dict, Any
from models.models import User

class UserCRUD:
    def __init__(self, db_session: AsyncSession):
        """
        UserCRUDクラスを初期化します
        
        Args:
            db_session: SQLAlchemy 非同期データベースセッション
        """
        self.db_session = db_session

    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        新規ユーザーを作成します
        
        Args:
            user_data: ユーザー情報を含む辞書
            
        Returns:
            作成されたユーザーオブジェクト
        """
        user = User(**user_data)
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        """
        指定IDのユーザーを取得します
        
        Args:
            user_id: 取得するユーザーのID
            
        Returns:
            ユーザーオブジェクト、または存在しない場合はNone
        """
        result = await self.db_session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        指定メールアドレスのユーザーを取得します
        
        Args:
            email: 取得するユーザーのメールアドレス
            
        Returns:
            ユーザーオブジェクト、または存在しない場合はNone
        """
        result = await self.db_session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """
        ユーザー情報を更新します
        
        Args:
            user_id: 更新するユーザーのID
            update_data: 更新する情報を含む辞書
            
        Returns:
            更新されたユーザーオブジェクト、または存在しない場合はNone
        """
        user = await self.get_user(user_id)
        if not user:
            return None
            
        for key, value in update_data.items():
            setattr(user, key, value)
            
        await self.db_session.commit()
        await self.db_session.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        """
        ユーザーを削除します
        
        Args:
            user_id: 削除するユーザーのID
            
        Returns:
            削除に成功した場合はTrue、それ以外はFalse
        """
        user = await self.get_user(user_id)
        if not user:
            return False
            
        await self.db_session.delete(user)
        await self.db_session.commit()
        return True