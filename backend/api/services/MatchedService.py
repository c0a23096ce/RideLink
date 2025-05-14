from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any
from services.Enums import UserStatus
from cruds.MatchCRUD import MatchCRUD
from services.ConnectionManager import ConnectionManager
import asyncio

class MatchedService:
    def __init__(self, db_session: Session, connection_manager: ConnectionManager):
        # データベースセッションを初期化
        self.db_session = db_session
        self.match_crud = MatchCRUD(db_session)
        self.connection_manager = connection_manager  # ConnectionManagerを追加
        self.lock = asyncio.Lock()  # ロックを初期化
    
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
    
    async def get_users_by_match(self, match_id: int) -> Optional[Dict[str, Any]]:
        """
        マッチIDからユーザー情報を取得する
        :param match_id: マッチID
        :return: ユーザー情報
        """
        # マッチIDからユーザー情報を取得
        users = await self.match_crud.get_users_by_match(match_id)
        if not users:
            return None
        
        return users
    
    async def report_ride_completion(self, match_id: int, user_id: int) -> Dict[str, Any]:
        """マッチング完了を報告"""
        async with self.lock:
            # マッチの存在確認
            try:
                await self.match_crud.update_match_user(match_id=match_id, user_id=user_id, user_status=UserStatus.COMPLETED)
            except Exception as e:
                return {"success": False, "error": f"DB削除に失敗しました: {str(e)}"}
            if self.connection_manager:
                # WebSocketを通じてユーザーにメッセージを送信
                await self.connection_manager.send_to_json_user(user_id, {"type": "status_update", "message": "ルート案内が完了しました"})
            
            return {"success": True, "message": "ルート案内が完了しました", "user_id": user_id}
        
    async def update_evaluation(self, match_id: int, user_id: int, evaluation_data: Dict[int, int]) -> Dict[str, Any]:
        """評価を更新"""
        async with self.lock:
            # マッチの存在確認
            try:
                await self.match_crud.update_evaluation(match_id=match_id, user_id=user_id, evaluation_data=evaluation_data)

                all_completed = await self.match_crud.check_all_completed(match_id=match_id)
                if all_completed:
                    # 全員が評価を完了した場合、Historyに保存、マッチを削除
                    match_dto = await self.match_crud.get_match(match_id=match_id)
                    match_users = await self.match_crud.get_users_by_match(match_id=match_dto.match_id)
                    await self.match_crud.save_to_match_history(match=match_dto)
                    for match_user in match_users:
                        await self.match_crud.save_to_match_user_history(user=match_user)
                    await self.match_crud.delete_match(match_id=match_id)
                    await self.match_crud.delete_match_users(match_id=match_id)
            except IntegrityError as e:
                return {"success": False, "error": f"DB削除に失敗しました: {str(e)}"}
            

            return {"success": True, "message": "評価が完了しました", "user_id": user_id}