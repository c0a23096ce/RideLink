from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List, Dict, Any

from api.models.models import User


class UserCRUD:
    def __init__(self, db_session: Session):
        """
        UserCRUDクラスを初期化します
        
        Args:
            db_session: SQLAlchemy データベースセッション
        """
        self.db_session = db_session

    def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        新規ユーザーを作成します
        
        Args:
            user_data: ユーザー情報を含む辞書
            
        Returns:
            作成されたユーザーオブジェクト
        """
        user = User(**user_data)
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """
        指定IDのユーザーを取得します
        
        Args:
            user_id: 取得するユーザーのID
            
        Returns:
            ユーザーオブジェクト、または存在しない場合はNone
        """
        return self.db_session.query(User).filter(User.user_id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        指定メールアドレスのユーザーを取得します
        
        Args:
            email: 取得するユーザーのメールアドレス
            
        Returns:
            ユーザーオブジェクト、または存在しない場合はNone
        """
        return self.db_session.query(User).filter(User.email == email).first()

    def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """
        ユーザー情報を更新します
        
        Args:
            user_id: 更新するユーザーのID
            update_data: 更新する情報を含む辞書
            
        Returns:
            更新されたユーザーオブジェクト、または存在しない場合はNone
        """
        user = self.get_user(user_id)
        if not user:
            return None
            
        for key, value in update_data.items():
            setattr(user, key, value)
            
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        """
        ユーザーを削除します
        
        Args:
            user_id: 削除するユーザーのID
            
        Returns:
            削除に成功した場合はTrue、それ以外はFalse
        """
        user = self.get_user(user_id)
        if not user:
            return False
            
        self.db_session.delete(user)
        self.db_session.commit()
        return True

    # def search_users(self, search_criteria: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[User]:
    #     """
    #     条件に基づいてユーザーを検索します
        
    #     Args:
    #         search_criteria: 検索条件の辞書
    #         skip: スキップするレコード数
    #         limit: 取得する最大レコード数
            
    #     Returns:
    #         ユーザーオブジェクトのリスト
    #     """
    #     query = self.db_session.query(User)
        
    #     # 検索条件を適用
    #     for key, value in search_criteria.items():
    #         if hasattr(User, key):
    #             query = query.filter(getattr(User, key).like(f"%{value}%"))
                
    #     # 名前とメールアドレスでの部分一致検索
    #     if "search_text" in search_criteria:
    #         search_text = search_criteria["search_text"]
    #         query = query.filter(
    #             or_(
    #                 User.name.like(f"%{search_text}%"),
    #                 User.email.like(f"%{search_text}%")
    #             )
    #         )
                
    #     # ページネーション
    #     return query.offset(skip).limit(limit).all()