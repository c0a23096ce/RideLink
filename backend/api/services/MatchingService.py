from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime, timedelta
from fastapi import WebSocket
from sqlalchemy.orm import Session
import asyncio
import time
import uuid
import random
from geopy.distance import geodesic 
from services.RouteGenerateService import RouteGenerateService
from config import settings
from models.models import Match, MatchUser
from cruds.MatchCRUD import MatchCRUD
from services.ConnectionManager import ConnectionManager
from services.Enums import UserRole, UserStatus, LobbyStatus

class UserData:
    """ユーザーのデータを保持するクラス"""
    def __init__(self, user_id: int, user_role: str, user_location: tuple, user_destination: tuple, user_status: str):
        self.user_id = user_id
        self.user_role = UserRole.DRIVER if user_role == UserRole.DRIVER else UserRole.PASSENGER
        self.user_location = user_location
        self.user_destination = user_destination
        self.user_status = user_status
        self.timestamp = time.time()
        
class RideLobby:
    """ドライバーが作成するロビー"""
    def __init__(self, 
                 lobby_id: int, 
                 driver_id: int, 
                 starting_location: Tuple[float, float],
                 destination: Optional[Tuple[float, float]],
                 user_status: str,
                 max_distance: float,
                 max_passengers: int,
                 preferences: Dict[str, Any] = {},
                 route_geojson: Optional[Dict] = None,  # ルートのGeoJSON
                 route_coordinates: Optional[List[Tuple[float, float]]] = None,  # ルート上の座標点リスト
                 ):
        self.lobby_id = lobby_id # ロビーID
        self.max_distance = max_distance # 最大距離
        self.max_passengers = max_passengers # 最大乗客数
        self.preferences = preferences # その他の設定
        self.created_at = time.time()
        self.status = LobbyStatus.OPEN
        # ルート情報を追加
        self.route_geojson = route_geojson
        self.route_coordinates = route_coordinates or []
        
        # ロビーの人物管理: {passenger_id: {"status": status, "timestamp": time, passenger_location: (lat, lng), passenger_destination: (lat, lng)}}
        # 承認状態も含む
        self.participants: Dict[int, UserData] = {driver_id: UserData(driver_id, UserRole.DRIVER, starting_location, destination, user_status)}
        
    def add_user(self, passenger_id: int, user_role: str, passenger_location: tuple, passenger_destination: tuple, user_status: str) -> bool:
        """ユーザーを追加"""
        # 新しいユーザーを追加
        self.participants[passenger_id] = UserData(
            user_id=passenger_id, 
            user_role=user_role, 
            user_location=passenger_location, 
            user_destination=passenger_destination,
            user_status=user_status
        )
        return True
        
    def is_full(self) -> bool:
        """ロビーが満員かどうか"""
        # ドライバーを除外して乗客数をカウント
        print(f"ロビー内の乗客数: {len(self.participants)-1}, 最大乗客数: {self.max_passengers}")
        return len(self.participants)-1 >= self.max_passengers
        
    def to_dict(self) -> Dict[str, Any]:
        """ロビー情報を辞書に変換"""
        return {
            "lobby_id": self.lobby_id,
            "max_distance": self.max_distance,
            "max_passengers": self.max_passengers,
            "current_users": len(self.participants),
            "status": self.status,
            "created_at": self.created_at,
            "preferences": self.preferences
        }
    
    def get_approve_status(self) -> bool:
        """承認状況を取得"""
        return all(request.user_status == UserStatus.APPROVED for request in self.participants.values())
    
    def get_driver(self) -> UserData:
        for user in self.participants.values():
            if user.user_role == UserRole.DRIVER:
                return user
        return None
    
    def get_passengers(self) -> List[UserData]:
        """乗客情報を取得"""
        return [user for user in self.participants.values() if user.user_role == UserRole.PASSENGER]

class MatchingService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db=None, connection_manager: ConnectionManager = None):
        if not self._initialized:
            self.ride_lobbies: Dict[str, RideLobby] = {}
            self.user_lobbies: Dict[int, str] = {}
            self.lock = asyncio.Lock()
            self.connection_manager = connection_manager  # ← 追加
            self._initialized = True

        if db is not None:
            self.set_db(db)

    def set_db(self, db: Session):
        self.db = db
        self.match_crud = MatchCRUD(self.db)
    
    def set_connection_manager(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """2点間の距離を計算"""
        if coord1 is None or coord2 is None:
            return float('inf')
        
        return geodesic(coord1, coord2).kilometers
    
    async def create_driver_lobby(self, 
                                driver_id: int,
                                starting_location: Tuple[float, float],
                                destination: Optional[Tuple[float, float]] = None,
                                max_distance: float = 5.0,
                                max_passengers: int = 1,
                                preferences: Dict[str, Any] = {}) -> Dict[str, Any]:
        """ドライバーがロビーを作成"""
        async with self.lock:
            # ドライバーが既にロビーを持っているか確認
            active_lobby = await self.match_crud.get_active_lobby_by_driver(driver_id)
            if active_lobby:
                return {"success": False, "error": "すでにロビーに所属しています"}
            
            # 出発地から目的地へのルートを生成
            route_geojson = None
            if (destination):
                route_service = RouteGenerateService(
                    api_key=settings.mapbox_api_key,
                    coordinates=[starting_location, destination],
                    
                    start_index=0,
                    end_index=1
                )
                route_data = await route_service.get_geojson_route()
                route_coordinates = []

                if route_data and 'routes' in route_data:
                    geometry = route_data['routes'][0]['geometry']
                    if geometry['type'] == 'LineString':
                        route_coordinates = [(coord[1], coord[0]) for coord in geometry['coordinates']]
            
            # DBにロビーを保存
            match_data = {
                "status": LobbyStatus.OPEN,
                "max_passengers": max_passengers,
                "max_distance": max_distance,
                "preferences": preferences if preferences else {},
                "route_geojson": route_geojson
            }
            try:
                match = await self.match_crud.create_match(match_data) # コミットはしていない
            except Exception as e:
                return {"success": False, "error": f"DB保存に失敗しました: {str(e)}"}
            
            driver_data = {
                "match_id": match.match_id,
                "user_id": driver_id,
                "user_start_lat": starting_location[0],
                "user_start_lng": starting_location[1],
                "user_destination_lat": destination[0] if destination else None,
                "user_destination_lng": destination[1] if destination else None,
                "user_status": UserStatus.IN_LOBBY,
                "user_role": UserRole.DRIVER
            }
            try:
                driver = await self.match_crud.add_match_user(driver_data) # ここでコミット
            except Exception as e:
                return {"success": False, "error": f"DB保存に失敗しました: {str(e)}"}
            
            # ロビー作成
            lobby = RideLobby(
                lobby_id=match.match_id,
                driver_id=driver.user_id,
                starting_location=(driver.user_start_lat, driver.user_start_lng),
                destination=(driver.user_destination_lat, driver.user_destination_lng),
                max_distance=match.max_distance,
                max_passengers=match.max_passengers,
                preferences=match.max_passengers,
                user_status=driver.user_status,
                route_geojson=route_data,
                route_coordinates=route_coordinates
            )
            
            # ロビーを登録
            self.ride_lobbies[match.match_id] = lobby
            self.user_lobbies[driver.user_id] = match.match_id
            
            return {
                "success": True,
                "lobby_id": match.match_id,
                "lobby": lobby.to_dict()
            }
    
    async def close_lobby(self, driver_id: int, lobby_id: str) -> Dict[str, Any]:
        """ドライバーがロビーを閉じる"""
        async with self.lock:
            # ロビーの存在確認
            if lobby_id not in self.ride_lobbies:
                return {"success": False, "error": "ロビーが存在しません"}
            
            lobby = self.ride_lobbies[lobby_id]
            
            # 権限チェック
            if lobby.get_driver().user_id != driver_id:
                return {"success": False, "error": "ロビーを閉じる権限がありません"}
            
            # ロビーを閉じる
            lobby.status = LobbyStatus.CLOSED
            
            # データベースでロビーを論理削除
            result = await self.match_crud.delete_match(lobby_id)
            if result == False:
                return {"success": False, "error": "データベース上のロビーが見つかりません"}
            
            # 関連するMatchUserレコードも論理削除
            result = await self.match_crud.delete_match_users(lobby_id)
            if result == False:
                return {"success": False, "error": "データベース上のロビーが見つかりません"}
            
            # 参加リクエスト中のユーザーに通知
            for passenger_id in lobby.participants:  # keyでループ
                if passenger_id != driver_id:  # ドライバーは除外
                    if self.connection_manager:
                        await self.connection_manager.send_to_json_user(passenger_id, {
                            "type": "status_update",
                            "lobby_id": lobby_id,
                            "message": "ドライバーがロビーを閉じました"
                        })
                        
                        # 乗客のロビー関連情報をクリア
                        if passenger_id in self.user_lobbies and self.user_lobbies[passenger_id] == lobby_id:
                            del self.user_lobbies[passenger_id]
            
            # ドライバーの情報もクリア
            del self.user_lobbies[driver_id]
            
            # ロビーを削除
            del self.ride_lobbies[lobby_id]
            
            return {"success": True}
    
    async def find_random_lobby_by_distance(self, 
                                        passenger_id: int, 
                                        passenger_location: Tuple[float, float],
                                        passenger_destination: Optional[Tuple[float, float]] = None,
                                        max_distance: float = 5.0) -> Optional[Dict[str, Any]]:
        """距離制限内のランダムなロビーを見つける（ドライバーのルートを考慮）"""
        async with self.lock:
            # 参加可能なロビーをフィルタリング
            available_lobbies = []
            
            for lobby in self.ride_lobbies.values():
                # オープン状態で満員でないロビーのみ対象
                if lobby.status != LobbyStatus.OPEN or lobby.is_full():
                    continue
                
                # 既にリクエスト済みのロビーは除外
                if passenger_id in lobby.participants:
                    continue
                
                driver_id = lobby.get_driver().user_id
                driver_data = lobby.participants[driver_id]
                
                # ルート情報があるか確認
                if not lobby.route_coordinates or len(lobby.route_coordinates) < 2:
                    # ルート情報がない場合は従来の距離計算
                    start_distance = await self.calculate_distance(passenger_location, driver_data.user_location)
                    
                    destination_distance = float('inf')
                    if passenger_destination and driver_data.user_destination:
                        destination_distance = await self.calculate_distance(passenger_destination, driver_data.user_destination)
                    
                    if start_distance <= max_distance and (destination_distance <= max_distance or passenger_destination is None):
                        available_lobbies.append({
                            "lobby": lobby,
                            "start_distance": start_distance,
                            "destination_distance": destination_distance if destination_distance != float('inf') else None,
                            "route_match": False
                        })
                    continue
                
                # 乗客の出発地がドライバーのルート上にあるか確認
                pickup_point_idx, pickup_distance = await self._find_closest_point_on_route(
                    passenger_location, 
                    lobby.route_coordinates, 
                    max_distance
                )
                
                if pickup_point_idx == -1:
                    continue  # ルート上に乗車地点が見つからない
                
                # 乗客の目的地がドライバーのルート上にあるか確認
                dropoff_point_idx = -1
                dropoff_distance = float('inf')
                
                if passenger_destination:
                    dropoff_point_idx, dropoff_distance = await self._find_closest_point_on_route(
                        passenger_destination,
                        lobby.route_coordinates,
                        max_distance
                    )
                    
                    # 目的地が見つからない場合はスキップ
                    if dropoff_point_idx == -1:
                        continue
                    
                    # 逆走防止: 乗車地点が降車地点よりも後にある場合はスキップ
                    if pickup_point_idx >= dropoff_point_idx:
                        continue
                
                # 条件を満たすロビーを追加
                available_lobbies.append({
                    "lobby": lobby,
                    "start_distance": pickup_distance,
                    "destination_distance": dropoff_distance if dropoff_distance != float('inf') else None,
                    "pickup_idx": pickup_point_idx,
                    "dropoff_idx": dropoff_point_idx,
                    "route_match": True
                })
            
            if not available_lobbies:
                return None
            
            # ルートマッチのあるロビーを優先
            route_matches = [l for l in available_lobbies if l.get("route_match", False)]
            
            if route_matches:
                # ルートマッチのあるロビーから選択
                # 出発地の距離が近い順にソート
                route_matches.sort(key=lambda x: x["start_distance"])
                
                # 距離が近い上位3つのロビーからランダムに選択
                top_count = min(3, len(route_matches))
                selected = random.choice(route_matches[:top_count])
            else:
                # ルートマッチがない場合は従来の方法で選択
                available_lobbies.sort(key=lambda x: x["start_distance"])
                top_count = min(3, len(available_lobbies))
                selected = random.choice(available_lobbies[:top_count])
            
            return {
                "lobby": selected["lobby"].to_dict(),
                "start_distance": selected["start_distance"],
                "destination_distance": selected["destination_distance"],
                "route_match": selected.get("route_match", False)
            }
    
    async def request_ride(self, passenger_id: int, lobby_id: int, passenger_location: tuple, passenger_destination: tuple) -> Dict[str, Any]:
        """乗車者がロビーに参加リクエスト"""
        async with self.lock:
            # ロビーの存在確認
            if lobby_id not in self.ride_lobbies:
                return {"success": False, "error": "ロビーが存在しません"}
            
            lobby = self.ride_lobbies[lobby_id]
            
            # ロビーのステータス確認
            if lobby.status != LobbyStatus.OPEN:
                return {"success": False, "error": "このロビーは参加を受け付けていません"}
            
            # すでに別のロビーに所属していないか確認
            if passenger_id in self.user_lobbies:
                return {"success": False, "error": "すでに別のロビーに所属しています"}
            
            # ロビーの最大乗客数を確認
            if lobby.is_full():
                return {"success": False, "error": "ロビーが満員です"}
            # 乗車リクエストを追加
            if passenger_id in lobby.participants:
                return {"success": False, "error": "すでにリクエスト済みです"}
            
            # データベースに乗客情報を保存
            user_data = {
                "match_id": lobby.lobby_id,
                "user_id": passenger_id,
                "user_start_lat": passenger_location[0],
                "user_start_lng": passenger_location[1],
                "user_destination_lat": passenger_destination[0],
                "user_destination_lng": passenger_destination[1],
                "user_status": UserStatus.IN_LOBBY,
                "user_role": UserRole.PASSENGER
            }
            
            try:
                user = await self.match_crud.add_match_user(user_data)  # データベースに保存
            except Exception as e:
                # データベース保存が失敗した場合、メモリから削除
                return {"success": False, "error": f"DB保存に失敗しました: {str(e)}"}
            
            lobby.add_user(passenger_id, UserRole.PASSENGER, (user.user_start_lat, user.user_start_lng), (user.user_destination_lat, user.user_destination_lng), user_status=user.user_status) # ロビーにリクエストを追加
            
            # ユーザーの持つロビーIDを追加
            self.user_lobbies[user.user_id] = user.match_id
            
            isfull = lobby.is_full()
            
            return {
                "success": True,
                "isfull": isfull,
                "message": "乗車リクエストを送信しました",
                "lobby": lobby.to_dict()
            }
    
    async def request_random_ride(self, 
                         passenger_id: int, 
                         passenger_location: Tuple[float, float],
                         passenger_destination: Optional[Tuple[float, float]] = None, 
                         max_distance: float = 5.0) -> Dict[str, Any]:
        """乗客が距離内のランダムなロビーに参加リクエスト（ドライバーのルートを考慮）"""
        # 距離内のランダムなロビーを見つける
        lobby_info = await self.find_random_lobby_by_distance(
            passenger_id, 
            passenger_location, 
            passenger_destination,
            max_distance
        )
        
        if not lobby_info:
            return {"success": False, "error": "条件に合うロビーが見つかりませんでした"}
        
        # 見つかったロビーにリクエスト
        lobby_id = lobby_info["lobby"]["lobby_id"]
        result = await self.request_ride(passenger_id, lobby_id, passenger_location, passenger_destination)
        
        # 距離情報と経路マッチ情報を追加
        if result["success"]:
            result["start_distance"] = lobby_info["start_distance"]
            result["destination_distance"] = lobby_info["destination_distance"]
            result["route_match"] = lobby_info.get("route_match", False)
        
            # ロビーが満員になった場合の処理
            if result["isfull"]:
                try:
                    await self.match_crud.update_match(match_id=lobby_id, status=LobbyStatus.WAITING_APPROVAL)
                except Exception as e:
                    return {"success": False, "error": f"DB更新に失敗しました: {str(e)}"}
                
                print("ロビーが満員になりました")
                lobby = self.ride_lobbies[lobby_id]
                participants = list(lobby.participants.keys())
                print(f"connection_manager: {self.connection_manager.active_connections}")
                # 全参加者に通知
                for user_id in participants:
                    if self.connection_manager:
                        await self.connection_manager.send_to_json_user(user_id, {
                            "type": "status_update",
                            "lobby_id": lobby_id,
                            "message": "ロビーが満員になりました。マッチングが確定しました。",
                        })
        
        return result

    async def cancel_ride_request(self, passenger_id: int, lobby_id: str = None) -> Dict[str, Any]:
        """乗車者がリクエストをキャンセル"""
        async with self.lock:
            # lobby_idが指定されていない場合は、ユーザーのロビーを使用
            if lobby_id is None:
                if passenger_id not in self.user_lobbies:
                    return {"success": False, "error": "ロビーに所属していません"}
                lobby_id = self.user_lobbies[passenger_id]
            
            # ロビーの存在確認
            if lobby_id not in self.ride_lobbies:
                return {"success": False, "error": "ロビーが存在しません"}
            
            lobby = self.ride_lobbies[lobby_id]
            
            # リクエストの存在確認
            if passenger_id not in lobby.participants:
                return {"success": False, "error": "リクエストが存在しません"}
            
            # 確定済みの場合はキャンセル不可
            if passenger_id in lobby.get_passengers() and lobby.participants[passenger_id].user_status == RequestStatus.CONFIRMED:
                return {"success": False, "error": "確定済みのリクエストはキャンセルできません"}
            
            # リクエストを削除
            del lobby.participants[passenger_id]
            
            # 乗客情報を削除
            if passenger_id in self.user_lobbies:
                del self.user_lobbies[passenger_id]
            
            return {"success": True, "message": "リクエストをキャンセルしました"}
    
    async def approve_ride(self, user_id: int, lobby_id: int):
        """マッチングした人を承認する"""
        async with self.lock:
        # ロビーの存在確認
            if lobby_id not in self.ride_lobbies:
                print(f"match_id_type: {type(lobby_id)}")
                return {"success": False, "error": "ロビーが存在しません"}
            
            lobby = self.ride_lobbies[lobby_id]
            
            # 権限とステータスチェック
            if user_id not in lobby.participants:
                return {"success": False, "error": "リクエストが存在しません"}
            
            # 承認処理
            try:
                await self.match_crud.update_match_user(match_id=lobby_id, user_id=user_id, user_status=UserStatus.APPROVED)
            except Exception as e:
                return {"success": False, "error": f"DB更新に失敗しました: {str(e)}"}
            self.ride_lobbies[lobby_id].participants[user_id].user_status = UserStatus.APPROVED
            
            # 双方承認済みかどうか
            is_confirmed = lobby.get_approve_status()
            print(f"承認状況: {lobby.get_approve_status()}")
            
            if is_confirmed:
                print("DBへのマッチ保存を開始")
                print(f"マッチング完了: {lobby.lobby_id} - ロビーのユーザー: {lobby.participants}")
                match = await self._complete_matching(lobby) # とりあえず今日はここまで。　続きはcomplete_matchingのDBステータスの更新
                return {"success": True, "match": match}
            
            return {"success": True, "message": "承認されましたが、まだ全員の承認が完了していません"}
    
    async def get_available_lobbies(self, passenger_location: Tuple[float, float], max_distance: float = 5.0) -> List[Dict[str, Any]]:
        """乗客が利用可能なロビー一覧を取得"""
        async with self.lock:
            available_lobbies = []
            
            for lobby in self.ride_lobbies.values():
                # オープン状態で満員でないロビーのみ対象
                if lobby.status != LobbyStatus.OPEN or lobby.is_full():
                    continue
                
                # 距離チェック
                distance = await self.calculate_distance(passenger_location, lobby.participants[lobby.get_driver().user_id].user_location)
                if distance <= max_distance:
                    lobby_info = lobby.to_dict()
                    lobby_info["distance"] = distance
                    available_lobbies.append(lobby_info)
            
            # 距離順にソート
            available_lobbies.sort(key=lambda x: x["distance"])
            
            return available_lobbies
    
    async def get_all_lobbies(self) -> List[Dict[str, Any]]:
        """全ロビー情報を取得"""
        async with self.lock:
            all_lobbies = []
            for lobby in self.ride_lobbies.values():
                all_lobbies.append(lobby.to_dict())
            return all_lobbies
    
    async def get_lobby_info(self, lobby_id: str) -> Dict[str, Any]:
        """ロビーの詳細情報を取得"""
        async with self.lock:
            if lobby_id not in self.ride_lobbies:
                return {"success": False, "error": "ロビーが存在しません"}
            
            lobby = self.ride_lobbies[lobby_id]
            return {
                "success": True,
                "lobby": lobby.to_dict(),
                "participants": [user.user_id for user in lobby.participants.values()]
            }
    
    async def get_lobby_users(self, lobby_id: int) -> List[int]:
        """ロビーに参加しているユーザーのIDを取得"""
        if lobby_id not in self.ride_lobbies:
            print(f"ロビーが存在しません: {lobby_id}")
            print(f"lobby_type: {type(lobby_id)}")
            return []
        
        lobby = self.ride_lobbies[lobby_id]
        return list(lobby.participants.keys()) # とりあえずドライバーと乗客のIDを返す
    
    async def _complete_matching(self, lobby: RideLobby) -> Match:
        """マッチングを完了してデータベースに保存"""
        # ロビーのステータスを更新
        print(f"マッチング完了: {lobby.lobby_id} - ロビーのユーザー: {lobby.participants}")
        try:
            match = await self.match_crud.update_match(match_id=lobby.lobby_id, status=lobby.status) # DBに保存
        except Exception as e:
            return {"success": False, "error": f"DB更新に失敗しました: {str(e)}"}
        
        # ロビーの参加者をマッチング済みに更新
        users = []
        for passenger_info in lobby.participants.values():
            users.append({"user_id": passenger_info.user_id, "user_status": UserStatus.MATCHED})
        try:
            await self.match_crud.update_match_users_bulk(match_id=lobby.lobby_id, users_data=users) # DBに保存
        except Exception as e:
            return {"success": False, "error": f"DB更新に失敗しました: {str(e)}"}
        
        # ロビーのステータスを更新
        lobby.status = match.status # ロビーのステータスを更新
        for user in users:
            lobby.participants[user["user_id"]].user_status = user["user_status"] # ロビーの参加者のステータスを更新
        
        # 案内ルートを生成
        coordinates = [lobby.get_driver().user_location]  # ドライバー出発地
        pickups_deliveries = []
        
        for i, (pid, info) in enumerate(lobby.participants.items()):
            coordinates.append(info.user_location)
            coordinates.append(info.user_destination)
            pickups_deliveries.append((1 + i * 2, 1 + i * 2 + 1))

        coordinates.append(lobby.get_driver().user_destination)  # ドライバーの目的地
        
        print(f"経路座標: {coordinates}")
        
        route_service = RouteGenerateService(
            api_key=settings.mapbox_api_key, # Mapbox APIキー
            coordinates=coordinates, # 経路座標
            pickups_deliveries=pickups_deliveries, # ピックアップとドロップオフの座標
            start_index=0, # ドライバーの出発地
            end_index=len(coordinates) - 1 # ドライバーの目的地
        )

        geodata = await route_service.get_geojson_route()

        if geodata:
            print("✔ 経路生成成功")
        else:
            print("❌ 経路生成に失敗しました")
        
        match_data = {
            "status": "Moving",
            "route_geojson": geodata
        }
        
        # DBに保存
        try:
            match = await self.match_crud.update_match(match_id=match.match_id, route_geojson=geodata, status=LobbyStatus.NAVIGATING)
        except Exception as e:
            return {"success": False, "error": f"DB更新に失敗しました: {str(e)}"}
        
        for passenger_info in lobby.participants.values():
            users.append({"user_id": passenger_info.user_id, "user_status": UserStatus.NAVIGATING})

        try:
            await self.match_crud.update_match_users_bulk(match_id=lobby.lobby_id, users_data=users)
        except Exception as e:
            return {"success": False, "error": f"DB更新に失敗しました: {str(e)}"}
        
        # 参加者全員に通知
        match_participants = list(lobby.participants.keys())
        
        for user_id in match_participants:
            # WebSocketで通知
            if self.connection_manager:
                print(f"送信するマッチID: {match.match_id}")
                await self.connection_manager.send_to_json_user(user_id, {
                    "type": "status_update",
                    "match_id": match.match_id,
                    "participants": match_participants
                })
            
            # ユーザー情報をクリア
            if user_id in self.user_lobbies:
                del self.user_lobbies[user_id]
        
        # ロビーを削除
        if lobby.lobby_id in self.ride_lobbies:
            del self.ride_lobbies[lobby.lobby_id]
        
        print(f"DBにマッチを保存: {match.match_id}")
        return match
    
    async def report_ride_completion(self, match_id: int) -> Dict[str, Any]:
        """マッチング完了を報告"""
        async with self.lock:
            # マッチの存在確認
            match = self.db.query(Match).filter(Match.match_id == match_id).first() # マッチIDでフィルタリング
            if not match:
                return {"success": False, "error": "マッチが存在しません"}
            
            # ステータスを更新
            match.status = "Completed"
            
            # データベースに保存
            self.db.commit()
            self.db.refresh(match)
            
            return {"success": True, "message": "ルート案内が完了しました", "match_id": match_id}

    async def _find_closest_point_on_route(self, 
                                     point: Tuple[float, float], 
                                     route_coordinates: List[Tuple[float, float]],
                                     max_distance: float) -> Tuple[int, float]:
        """
        ルート上で指定された点に最も近い点のインデックスと距離を返す
        
        Args:
            point: 基準点の座標 (lat, lng)
            route_coordinates: ルート上の座標点リスト [(lat, lng), ...]
            max_distance: 許容最大距離（km）
            
        Returns:
            (最も近い点のインデックス, 距離) - 見つからない場合は (-1, inf)
        """
        if not route_coordinates:
            return -1, float('inf')
        
        min_distance = float('inf')
        closest_idx = -1
        
        for i, route_point in enumerate(route_coordinates):
            distance = await self.calculate_distance(point, route_point)
            if distance < min_distance:
                min_distance = distance
                closest_idx = i
        
        if min_distance <= max_distance:
            return closest_idx, min_distance
        else:
            return -1, float('inf')