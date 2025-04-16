from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List, Dict, Any
from models.models import Match, MatchUser

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
        return match
    
    def add_match_users(self, match_users: List[MatchUser]):
        """マッチにユーザーを追加します
        
        Args:
            match_users: マッチユーザー情報を含むリスト
            
        Returns:
            作成されたマッチユーザーオブジェクトのリスト
        """
        self.db_session.add_all(match_users)
        return match_users