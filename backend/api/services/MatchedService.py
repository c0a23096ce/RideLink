from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any

from cruds.MatchCRUD import MatchCRUD

class MatchedService:
    def __init__(self, db_session: Session):
        # データベースセッションを初期化
        self.db_session = db_session
        # UserCRUDインスタンスを作成
        self.match_crud = MatchCRUD(db_session)
    
    async def get_match_id(self, user_id: int) -> Optional[int]:
        """
        ユーザーのマッチIDを取得する
        :param user_id: ユーザーID
        :return: マッチID
        """
        # ユーザーのマッチ情報を取得
        match_user = self.match_crud.get_match(user_id)
        if not match_user:
            return None
        return match_user.match_id
    
    async def get_matched_route(self, match_id: int) -> Optional[Dict[str, Any]]:
        """
        マッチングされたルートを取得する
        :param match_id: マッチID
        :return: マッチングされたルートの情報
        """
        # マッチIDからマッチング情報を取得
        match = self.match_crud.get_match(match_id)
        if not match:
            return None
        
        return match.route_geojson