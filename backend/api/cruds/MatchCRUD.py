from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Dict, Any
from models.models import Match, MatchUser
from services.Enums import UserRole
from dto.MatchDTO import MatchDTO, MatchUserDTO

class MatchCRUD:
    def __init__(self, db_session: AsyncSession):
        """
        MatchCRUDクラスを初期化します
        
        Args:
            db_session: SQLAlchemy 非同期データベースセッション
        """
        self.db_session = db_session
    
    async def get_match(self, match_id: int) -> Optional[MatchDTO]:
        """
        ユーザーのルートを取得する
        
        Args:
            match_id: マッチID
        
        Returns:
            マッチDTO
        """
        result = await self.db_session.execute(
            select(Match).where(Match.match_id == match_id, Match.is_deleted == False)
        )
        match = result.scalar_one_or_none()
        if not match:
            return None
        
        return MatchDTO(
            match_id=match.match_id,
            status=match.status,
            route_geojson=match.route_geojson,
            max_passengers=match.max_passengers,
            max_distance=match.max_distance,
            preferences=match.preferences,
            is_deleted=match.is_deleted,
            created_at=match.created_at.isoformat() if match.created_at else None,
            updated_at=match.updated_at.isoformat() if match.updated_at else None,
        )
    
    async def get_match_raw(self, match_id: int) -> Optional[MatchDTO]:
        """
        ユーザーのルートを取得する
        
        Args:
            match_id: マッチID
        
        Returns:
            マッチDTO
        """
        result = await self.db_session.execute(
            select(Match).where(Match.match_id == match_id, Match.is_deleted == False)
        )
        match = result.scalar_one_or_none()
        if not match:
            return None
        
        return match
    
    async def get_match_by_user(self, user_id: int) -> Optional[MatchUserDTO]:
        """
        ユーザーのマッチIDを取得する
        
        Args:
            user_id: ユーザーID
        
        Returns:
            マッチユーザーDTO
        """
        result = await self.db_session.execute(
            select(MatchUser).where(MatchUser.user_id == user_id, MatchUser.is_deleted == False)
        )
        match_user = result.scalar_one_or_none()
        if not match_user:
            return None
        await self.db_session.refresh(match_user)
        return MatchUserDTO(
            id=match_user.id,
            match_id=match_user.match_id,
            user_id=match_user.user_id,
            user_start_lat=match_user.user_start_lat,
            user_start_lng=match_user.user_start_lng,
            user_destination_lat=match_user.user_destination_lat,
            user_destination_lng=match_user.user_destination_lng,
            user_role=match_user.user_role,
            user_status=match_user.user_status,
            is_deleted=match_user.is_deleted,
            created_at=match_user.created_at.isoformat() if match_user.created_at else None,
            updated_at=match_user.updated_at.isoformat() if match_user.updated_at else None,
        )
    
    async def create_match(self, match_data: Dict[str, Any]) -> MatchDTO:
        """
        新規マッチを作成します
        
        Args:
            match_data: マッチ情報を含む辞書
            
        Returns:
            作成されたマッチDTOオブジェクト
        """
        match = Match(**match_data)
        self.db_session.add(match)
        await self.db_session.flush()  # コミットは外側でやる設計
        await self.db_session.refresh(match)

        return MatchDTO(
            match_id=match.match_id,
            status=match.status,
            route_geojson=match.route_geojson,
            max_passengers=match.max_passengers,
            max_distance=match.max_distance,
            preferences=match.preferences,
            is_deleted=match.is_deleted,
            created_at=match.created_at.isoformat() if match.created_at else None,
            updated_at=match.updated_at.isoformat() if match.updated_at else None,
        )
    
    async def add_match_user(self, match_user_data: Dict[str, Any]) -> MatchUserDTO:
        """
        マッチにユーザーを追加します
        
        Args:
            match_user_data: マッチユーザー情報
            
        Returns:
            作成されたマッチユーザーDTOオブジェクト
        """
        match_user = MatchUser(**match_user_data)
        self.db_session.add(match_user)
        await self.db_session.commit()
        
        await self.db_session.refresh(match_user)

        return MatchUserDTO(
            id=match_user.id,
            match_id=match_user.match_id,
            user_id=match_user.user_id,
            user_start_lat=match_user.user_start_lat,
            user_start_lng=match_user.user_start_lng,
            user_destination_lat=match_user.user_destination_lat,
            user_destination_lng=match_user.user_destination_lng,
            user_role=match_user.user_role,
            user_status=match_user.user_status,
            is_deleted=match_user.is_deleted,
            created_at=match_user.created_at.isoformat() if match_user.created_at else None,
            updated_at=match_user.updated_at.isoformat() if match_user.updated_at else None,
        )
    
    async def get_active_lobby_by_driver(self, driver_id: int) -> Optional[Match]:
        """
        ドライバーが現在アクティブなロビーを持っているか確認
        """
        result = await self.db_session.execute(
            select(Match).join(MatchUser).where(
                MatchUser.user_id == driver_id,
                MatchUser.user_role == UserRole.DRIVER,
                Match.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def update_match(self, match_id: int, **kwargs) -> Optional[Match]:
        """
        マッチの情報を更新する汎用メソッド
        """
        match = await self.get_match_raw(match_id)
        if not match:
            return None
        
        for key, value in kwargs.items():
            if hasattr(match, key):
                setattr(match, key, value)
        
        await self.db_session.commit()
        await self.db_session.refresh(match)
        return MatchDTO(
            match_id=match.match_id,
            status=match.status,
            route_geojson=match.route_geojson,
            max_passengers=match.max_passengers,
            max_distance=match.max_distance,
            preferences=match.preferences,
            is_deleted=match.is_deleted,
            created_at=match.created_at.isoformat() if match.created_at else None,
            updated_at=match.updated_at.isoformat() if match.updated_at else None,
        )

    async def update_match_user(self, match_id: int, user_id: int, **kwargs) -> Optional[MatchUser]:
        """
        マッチユーザーの情報を更新する汎用メソッド
        """
        result = await self.db_session.execute(
            select(MatchUser).where(
                MatchUser.match_id == match_id,
                MatchUser.user_id == user_id,
                MatchUser.is_deleted == False
            )
        )
        match_user = result.scalar_one_or_none()
        if not match_user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(match_user, key):
                setattr(match_user, key, value)
        
        await self.db_session.commit()
        return match_user

    async def delete_match(self, match_id: int) -> bool:
        """
        指定されたマッチを論理削除
        """
        match = await self.get_match(match_id)
        if not match:
            return False
        
        match.is_deleted = True
        await self.db_session.commit()
        return True

    async def delete_match_users(self, match_id: int) -> bool:
        """
        指定されたマッチに関連するユーザーを論理削除
        """
        result = await self.db_session.execute(
            select(MatchUser).where(MatchUser.match_id == match_id)
        )
        match_users = result.scalars().all()
        if not match_users:
            return False
        
        for match_user in match_users:
            match_user.is_deleted = True
        await self.db_session.commit()
        return True

    async def update_match_users_bulk(self, match_id: int, users_data: List[Dict[str, Any]]) -> bool:
        """
        数のマッチユーザー情報を一括で更新するメソッド
        """
        try:
            for user_data in users_data:
                user_id = user_data.get("user_id")
                if not user_id:
                    continue

                result = await self.db_session.execute(
                    select(MatchUser).where(
                        MatchUser.match_id == match_id,
                        MatchUser.user_id == user_id,
                        MatchUser.is_deleted == False
                    )
                )
                match_user = result.scalar_one_or_none()
                if not match_user:
                    continue

                for key, value in user_data.items():
                    if key != "user_id" and hasattr(match_user, key):
                        setattr(match_user, key, value)

            await self.db_session.commit()
            return True
        except Exception as e:
            await self.db_session.rollback()
            print(f"Error updating match users in bulk: {e}")
            return False
