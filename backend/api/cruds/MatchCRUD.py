from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List, Dict, Any
from models.models import Match, MatchUser
from services.Enums import UserRole

class MatchCRUD:
    def __init__(self, db_session: Session):
        """UserCRUDクラスを初期化します
        
        Args:
            db_session: SQLAlchemy データベースセッション
        
        """
        self.db_session = db_session
    
    def get_match(self, match_id: int) -> Optional[Dict[str, Any]]:
        """ユーザーのルートを取得する
        Args:
            match_id: マッチID
        Returns:
            マッチ情報
        """
        # ここにルートを取得するためのロジックを実装
        return self.db_session.query(Match).filter(Match.match_id == match_id).first()
    
    def get_match_by_user(self, user_id: int):
        """ユーザーのマッチIDを取得する
        Args:
            user_id: ユーザーID
        Returns:
            ユーザーのマッチ情報
        """
        return self.db_session.query(MatchUser).filter(MatchUser.user_id == user_id).first()
    
    def create_match(self, match_data: Dict[str, Any]) -> Match:
        """新規マッチを作成します
        
        Args:
            match_data: マッチ情報を含む辞書
            
        Returns:
            作成されたマッチオブジェクト
        """
        match = Match(**match_data)
        self.db_session.add(match)
        self.db_session.flush() # ユーザー保存までとトランザクションとして扱いたいためコミットはしない
        return match
    
    def add_match_user(self, match_user: Dict[str, Any]):
        """マッチにユーザーを追加します
        
        Args:
            match_users: マッチユーザー情報
            
        Returns:
            作成されたマッチユーザーオブジェクト
        """
        match_user = MatchUser(**match_user)
        self.db_session.add(match_user)
        self.db_session.commit()
        return match_user
    
    def add_match_users(self, match_users: List[MatchUser]):
        """マッチに一括でユーザーを追加します
        
        Args:
            match_users: マッチユーザー情報を含むリスト
            
        Returns:
            作成されたマッチユーザーオブジェクトのリスト
        """
        self.db_session.add_all(match_users)
        return match_users
    
    def get_active_lobby_by_driver(self, driver_id: int) -> Optional[Match]:
        """ドライバーが現在アクティブなロビーを持っているか確認"""
        return self.db_session.query(Match).join(MatchUser).filter(
            MatchUser.user_id == driver_id,
            MatchUser.user_role == UserRole.DRIVER,
            Match.is_deleted == 0  # アクティブな状態を示すステータス
        ).first()

    # def update_match_status(self, match_id: int, status: str) -> bool:
    #     """マッチのステータスを更新"""
    #     match = self.db_session.query(Match).filter(
    #         Match.match_id == match_id
    #     ).first()
    #     if not match:
    #         return False
    #     match.status = status
    #     self.db_session.commit()
    #     return match
    
    def update_match(self, match_id: int, **kwargs) -> Optional[Match]:
        """マッチの情報を更新する汎用メソッド"""
        match = self.db_session.query(Match).filter(
            Match.match_id == match_id,
            Match.is_deleted == False # 念のため論理削除されていないマッチを確認
            ).first()
        if not match:
            return False
        
        # 渡されたフィールドを更新
        for key, value in kwargs.items():
            if hasattr(match, key):
                setattr(match, key, value)
        
        self.db_session.commit()
        return match
    
    # def update_user_status(self, match_id: int, user_id: int, status: str) -> bool:
    #     """ユーザーのステータスを更新"""
    #     match_user = self.db_session.query(MatchUser).filter(
    #         MatchUser.match_id == match_id,
    #         MatchUser.user_id == user_id,
    #         MatchUser.is_deleted == False # 念のため論理削除されていないユーザーを確認
    #     ).first()
    #     if not match_user:
    #         return False
    #     match_user.status = status
    #     self.db_session.commit()
    #     return True

    def update_match_user(self, match_id: int, user_id: int, **kwargs) -> bool:
        """マッチユーザーの情報を更新する汎用メソッド"""
        match_user = self.db_session.query(MatchUser).filter(
            MatchUser.match_id == match_id,
            MatchUser.user_id == user_id,
            MatchUser.is_deleted == False # 念のため論理削除されていないユーザーを確認
        ).first()
        if not match_user:
            return False
        
        # 渡されたフィールドを更新
        for key, value in kwargs.items():
            if hasattr(match_user, key):
                setattr(match_user, key, value)
        
        self.db_session.commit()
        return match_user

    def delete_match(self, match_id: int) -> bool:
        """指定されたマッチを論理削除"""
        match = self.db_session.query(Match).filter(Match.match_id == match_id).first()
        if not match:
            return False
        match.is_deleted = True
        self.db_session.commit()
        return True

    def delete_match_users(self, match_id: int) -> bool:
        """指定されたマッチに関連するユーザーを論理削除"""
        match_users = self.db_session.query(MatchUser).filter(MatchUser.match_id == match_id).all()
        if not match_users:
            return False
        for match_user in match_users:
            match_user.is_deleted = True
        self.db_session.commit()
        return True

    def update_match_users_bulk(self, match_id: int, users_data: List[Dict[str, Any]]) -> bool:
        """数のマッチユーザー情報を一括で更新するメソッド"""
        try:
            for user_data in users_data:
                user_id = user_data.get("user_id")
                if not user_id:
                    continue  # user_idがない場合はスキップ

                match_user = self.db_session.query(MatchUser).filter(
                    MatchUser.match_id == match_id,
                    MatchUser.user_id == user_id,
                    MatchUser.is_deleted == False  # 論理削除されていないユーザーを確認
                ).first()

                if not match_user:
                    continue  # 該当ユーザーが見つからない場合はスキップ

                # 渡されたフィールドを更新
                for key, value in user_data.items():
                    if key != "user_id" and hasattr(match_user, key):
                        setattr(match_user, key, value)

            self.db_session.commit()
            return True
        except Exception as e:
            self.db_session.rollback()  # エラーが発生した場合はロールバック
            print(f"Error updating match users in bulk: {e}")
            return False
