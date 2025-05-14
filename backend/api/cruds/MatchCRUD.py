from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Dict, Any
from models.models import Match, MatchUser, MatchHistory, MatchUsersHistory, Evaluation
from services.Enums import UserRole, EvaluationStatus
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
            select(Match).where(Match.match_id == match_id)
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
            created_at=match.created_at.isoformat() if match.created_at else None,
            updated_at=match.updated_at.isoformat() if match.updated_at else None,
        )
    
    async def get_users_by_match(self, match_id: int) -> List[MatchUserDTO]:
        """
        マッチIDからユーザー情報を取得する
        
        Args:
            match_id: マッチID
        
        Returns:
            ユーザーDTOのリスト
        """
        result = await self.db_session.execute(
            select(MatchUser).where(MatchUser.match_id == match_id)
        )
        match_users = result.scalars().all()
        
        return [
            MatchUserDTO(
                id=match_user.id,
                match_id=match_user.match_id,
                user_id=match_user.user_id,
                user_start_lat=match_user.user_start_lat,
                user_start_lng=match_user.user_start_lng,
                user_destination_lat=match_user.user_destination_lat,
                user_destination_lng=match_user.user_destination_lng,
                user_role=match_user.user_role,
                user_status=match_user.user_status,
                created_at=match_user.created_at.isoformat() if match_user.created_at else None,
                updated_at=match_user.updated_at.isoformat() if match_user.updated_at else None,
            )
            for match_user in match_users
        ]
        
    
    async def get_match_raw(self, match_id: int) -> Optional[MatchDTO]:
        """
        ユーザーのルートを取得する
        
        Args:
            match_id: マッチID
        
        Returns:
            マッチDTO
        """
        result = await self.db_session.execute(
            select(Match).where(Match.match_id == match_id)
        )
        match = result.scalar_one_or_none()
        if not match:
            return None
        
        return match
    
    async def get_match_by_user(self, user_id: int) -> Optional[MatchUserDTO]:
        """
        ユーザーのマッチ情報を取得する
        
        Args:
            user_id: ユーザーID
        
        Returns:
            マッチユーザーDTO
        """
        result = await self.db_session.execute(
            select(MatchUser).where(MatchUser.user_id == user_id)
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
            created_at=match_user.created_at.isoformat() if match_user.created_at else None,
            updated_at=match_user.updated_at.isoformat() if match_user.updated_at else None,
        )
    
    async def get_active_lobby_by_driver(self, driver_id: int) -> Optional[Match]:
        """
        ドライバーが現在アクティブなロビーを持っているか確認

        Args:
            driver_id: ドライバーのユーザーID
        
        Returns:
            アクティブなマッチオブジェクト
        """
        result = await self.db_session.execute(
            select(Match).join(MatchUser).where(
                MatchUser.user_id == driver_id,
                MatchUser.user_role == UserRole.DRIVER,
            )
        )
        return result.scalar_one_or_none()

    async def update_match(self, match_id: int, **kwargs) -> Optional[Match]:
        """
        マッチの情報を更新する汎用メソッド

        Args:
            match_id: マッチID
            **kwargs: 更新するフィールドとその値
        
        Returns:
            更新されたマッチDTOオブジェクト
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
            created_at=match.created_at.isoformat() if match.created_at else None,
            updated_at=match.updated_at.isoformat() if match.updated_at else None,
        )

    async def update_match_user(self, match_id: int, user_id: int, **kwargs) -> Optional[MatchUser]:
        """
        マッチユーザーの情報を更新する汎用メソッド

        Args:
            match_id: マッチID
            user_id: ユーザーID
            **kwargs: 更新するフィールドとその値
        
        Returns:
            更新されたマッチユーザーDTOオブジェクト
        """
        result = await self.db_session.execute(
            select(MatchUser).where(
                MatchUser.match_id == match_id,
                MatchUser.user_id == user_id
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
        指定されたマッチを物理削除

        Args:
            match_id: マッチID
        
        Returns:
            bool: 削除成功ならTrue、失敗ならFalse
        """
        result = await self.db_session.execute(
            select(Match).where(Match.match_id == match_id)
        )
        match = result.scalar_one_or_none()
        if not match:
            return False

        await self.db_session.delete(match)
        await self.db_session.commit()
        return True

    async def delete_match_users(self, match_id: int) -> bool:
        """
        指定されたマッチのユーザーを物理削除

        Args:
            match_id: マッチID
        
        Returns:
            bool: 削除成功ならTrue、失敗ならFalse
        """
        result = await self.db_session.execute(
            select(MatchUser).where(MatchUser.match_id == match_id)
        )
        match_users = result.scalars().all()
        if not match_users:
            return False

        for match_user in match_users:
            await self.db_session.delete(match_user)
        
        await self.db_session.commit()
        return True
        

    async def update_match_users_bulk(self, match_id: int, users_data: List[Dict[int, Any]]) -> bool:
        """
        数のマッチユーザー情報を一括で更新するメソッド

        Args:
            match_id: マッチID
            users_data: 更新するユーザーデータのリスト
        
        Returns:
            bool: 更新成功ならTrue、失敗ならFalse
        """
        for user_data in users_data:
            user_id = user_data.get("user_id")
            if not user_id:
                continue

            result = await self.db_session.execute(
                select(MatchUser).where(
                    MatchUser.match_id == match_id,
                    MatchUser.user_id == user_id
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

    async def save_to_match_history(self, match: MatchDTO) -> None:
        match_history = MatchHistory(
            match_id=match.match_id,
            status=match.status,
            route_geojson=match.route_geojson,
            max_passengers=match.max_passengers,
            max_distance=match.max_distance,
            preferences=match.preferences,
            created_at=match.created_at,
            completed_at=match.updated_at
        )
        self.db_session.add(match_history)
        await self.db_session.commit()
        return
    
    async def save_to_match_user_history(self, user: MatchUserDTO) -> None:
        user_history = MatchUsersHistory(
            match_id=user.match_id,
            user_id=user.user_id,
            user_start_lat=user.user_start_lat,
            user_start_lng=user.user_start_lng,
            user_destination_lat=user.user_destination_lat,
            user_destination_lng=user.user_destination_lng,
            user_role=user.user_role,
            user_status=user.user_status,
            created_at=user.created_at,
            completed_at=user.updated_at
        )
        self.db_session.add(user_history)
        await self.db_session.commit()
        return
    
    async def save_to_match_users_history(self, match_users: List[MatchUserDTO]) -> None:
        for user in match_users:
            user_history = MatchUsersHistory(
                match_id=user.match_id,
                user_id=user.user_id,
                user_start_lat=user.user_start_lat,
                user_start_lng=user.user_start_lng,
                user_destination_lat=user.user_destination_lat,
                user_destination_lng=user.user_destination_lng,
                user_role=user.user_role,
                user_status=user.user_status,
                created_at=user.created_at,
                completed_at=user.updated_at
            )
            self.db_session.add(user_history)
        await self.db_session.commit()
        return

    async def create_evaluation_bulk(self, match_id: int, evaluations_data: list[Dict[str, int]]) -> None:
        """
        マッチの評価を保存領域を作成するメソッド

        Args:
            match_id: マッチID
            evaluations_data: ユーザーIDの辞書
        
        Returns:
            None
        """
        user_ids = evaluations_data.get("user_ids", [])
        evaluations = []
        # 各ユーザーが他のユーザーを評価するペアを作成
        for evaluator_id in user_ids:
            for evaluatee_id in user_ids:
                if evaluator_id != evaluatee_id:  # 自分自身を評価しない
                    evaluation = Evaluation(
                        match_id=match_id,
                        evaluator_id=evaluator_id,
                        evaluatee_id=evaluatee_id,
                        status=EvaluationStatus.WAITING
                    )
                    evaluations.append(evaluation)
        
        # データベースに一括追加
        self.db_session.add_all(evaluations)
        await self.db_session.commit()

    async def get_not_evaluated_list(self, match_id: int, user_id: int) -> Optional[List[Evaluation]]:
        """
        未評価のマッチを取得するメソッド

        Args:
            user_id: ユーザーID
            match_id: マッチID
        
        Returns:
            評価のリスト
        """
        result = await self.db_session.execute(
            select(Evaluation).where(
                Evaluation.match_id == match_id, 
                Evaluation.evaluator_id == user_id,
                Evaluation.status == EvaluationStatus.WAITING)
        )
        evaluations = result.scalars().all()
        
        return evaluations
    
    async def check_all_reviewed(self, match_id: int) -> bool:
        """
        全ての評価が完了しているか確認するメソッド

        Args:
            match_id: マッチID
        
        Returns:
            bool: 全ての評価が完了しているならTrue、そうでなければFalse
        """
        result = await self.db_session.execute(
            select(Evaluation).where(
                Evaluation.match_id == match_id,
                Evaluation.status == EvaluationStatus.WAITING
            )
        )
        evaluations = result.scalars().all()
        
        return len(evaluations) == 0

    async def get_user_evaluation(self, match_id: int, user_id: int) -> Optional[List[Evaluation]]:
        """
        ユーザーの評価を取得するメソッド

        Args:
            match_id: マッチID
        
        Returns:
            評価のリスト
        """
        result = await self.db_session.execute(
            select(Evaluation).where(
                Evaluation.match_id == match_id,
                Evaluation.status == EvaluationStatus.COMPLETED,
                Evaluation.evaluator_id == user_id
            )
        )
        evaluations = result.scalars().all()
        
        return evaluations

    async def update_evaluation(self, match_id: int, user_id: int, evaluation_data: Dict[int, int]) -> None:
        """
        マッチの評価を更新するメソッド

        Args:
            match_id: マッチID
            user_id: ユーザーID
            evaluation_data: 評価情報を含む辞書
        
        Returns:
            bool: 更新成功ならTrue、失敗ならFalse
        """
        evaluations = await self.get_not_evaluated_list(match_id=match_id, user_id=user_id) # 未評価のリストを取得
        if not evaluations:
            return
        
        for evaluation in evaluations:
            if evaluation.evaluatee_id in evaluation_data:
                evaluation.status = EvaluationStatus.COMPLETED
                evaluation.rating = evaluation_data[evaluation.evaluatee_id]
        await self.db_session.commit()
        return True