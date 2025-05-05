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
        match_user = await self.match_crud.get_match_by_user(user_id)
        match_data = await self.match_crud.get_match(match_user.match_id) if match_user else None
        if not match_data:
            return None
        return match_data.match_id
    
    async def get_user_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        ユーザーのマッチング状況を取得する
        :param user_id: ユーザーID
        :return: マッチング状況
        """
        # ユーザーのマッチ情報を取得
        match_user = await self.match_crud.get_match_by_user(user_id)
        if not match_user:
            return None
        
        return match_user.user_status
    
    async def get_matched_route(self, match_id: int) -> Optional[Dict[str, Any]]:
        """
        マッチングされたルートを取得する
        :param match_id: マッチID
        :return: マッチングされたルートの情報
        """
        # マッチIDからマッチング情報を取得
        match = await self.match_crud.get_match(match_id)
        if not match:
            return None
        
        return match.route_geojson