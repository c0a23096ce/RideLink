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
from models.models import Match, MatchPassenger

class UserRole:
    """ユーザーの役割を定義する定数"""
    DRIVER = "driver"
    PASSENGER = "passenger"

class RequestStatus:
    """リクエストのステータスを定義する定数"""
    PENDING = "pending"      # 申請中
    CONFIRMED = "confirmed"  # 双方確認済み

class LobbyStatus:
    """ロビーのステータスを定義する定数"""
    OPEN = "open"            # 参加者募集中
    MATCHING = "matching"    # マッチング中
    COMPLETED = "completed"  # マッチング完了
    CLOSED = "closed"        # 閉鎖済み

class UserData:
    """ユーザーのデータを保持するクラス"""
    def __init__(self, user_id: int, user_role: str, user_location: tuple, user_destination: tuple):
        self.user_id = user_id
        self.user_role = UserRole.DRIVER if user_role == UserRole.DRIVER else UserRole.PASSENGER
        self.user_location = user_location
        self.user_destination = user_destination
        self.user_status = RequestStatus.PENDING
        self.timestamp = time.time()
        
class RideLobby:
    """ドライバーが作成するロビー"""
    def __init__(self, 
                 lobby_id: str, 
                 driver_id: int, 
                 starting_location: Tuple[float, float],
                 destination: Optional[Tuple[float, float]],
                 max_distance: float = 5.0,
                 max_passengers: int = 1,
                 preferences: Dict[str, Any] = {}):
        self.lobby_id = lobby_id # ロビーID
        self.max_distance = max_distance # 最大距離
        self.max_passengers = max_passengers # 最大乗客数
        self.preferences = preferences # その他の設定
        self.created_at = time.time()
        self.status = LobbyStatus.OPEN
        
        # ロビーの人物管理: {passenger_id: {"status": status, "timestamp": time, passenger_location: (lat, lng), passenger_destination: (lat, lng)}}
        # 承認状態も含む
        self.participants: Dict[int, UserData] = {driver_id: UserData(driver_id, UserRole.DRIVER, starting_location, destination)}
        
    def add_request(self, passenger_id: int, passenger_location: tuple, passenger_destination: tuple) -> bool:
        """乗車リクエストを追加"""
        # すでに満員の場合は拒否
        if len(self.participants) >= self.max_passengers:
            return False
            
        # すでにリクエスト済みの場合
        if passenger_id in self.participants:
            return False
            
        # 新しいリクエストを追加
        self.participants[passenger_id] = UserData(
            passenger_id, 
            UserRole.PASSENGER, 
            passenger_location, 
            passenger_destination
        )
        return True
        
    def is_full(self) -> bool:
        """ロビーが満員かどうか"""
        print(f"ロビー内の乗客数: {len(self.participants)}, 最大乗客数: {self.max_passengers}")
        return len(self.participants) >= self.max_passengers
        
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
        return all(request.user_status == RequestStatus.CONFIRMED for request in self.participants.values())
    
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
    
    def __init__(self, db=None):
        if not self._initialized:
            self.db = db
            self.ride_lobbies: Dict[str, RideLobby] = {} # ロビーIDとロビーの対応
            self.user_lobbies: Dict[int, str] = {} # ユーザーIDとロビーIDの対応
            self._initialized = True
            self.active_connections: Dict[int, WebSocket] = {}  # ユーザーIDとWebSocketの対応

        elif db is not None:
            self.db = db  # DBオブジェクトは常に更新

        self.lock = asyncio.Lock()  # 排他制御用ロック
        
    async def register_connection(self, user_id: int, websocket: WebSocket):
        """WebSocket接続を登録"""
        self.active_connections[user_id] = websocket
        print(f"User {user_id}を接続しました")
        print(f"現在の接続: {self.active_connections}")
        
    async def unregister_connection(self, user_id: int):
        """WebSocket接続を解除"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            
            # ユーザーが所属するロビーから退出処理
            if user_id in self.user_lobbies:
                lobby_id = self.user_lobbies[user_id]
                if user_id in self.user_roles and self.user_roles[user_id] == UserRole.DRIVER:
                    await self.close_lobby(user_id, lobby_id)
                else:
                    await self.cancel_ride_request(user_id, lobby_id)
    
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
            if driver_id in self.user_lobbies:
                return {"success": False, "error": "すでにロビーに所属しています"}
            
            # 新しいロビーIDを生成
            lobby_id = str(uuid.uuid4())
            
            # ロビー作成
            lobby = RideLobby(
                lobby_id=lobby_id, # ロビーID
                driver_id=driver_id, # ドライバーID
                starting_location=starting_location, # 出発地
                destination=destination, # 目的地
                max_distance=max_distance, # 最大距離
                max_passengers=max_passengers, # 最大乗客数
                preferences=preferences # その他の設定
            )
            
            # ロビーを登録
            self.ride_lobbies[lobby_id] = lobby
            self.user_lobbies[driver_id] = lobby_id # ドライバーが所属するロビーを登録
            
            return {
                "success": True,
                "lobby_id": lobby_id,
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
            
            # 参加リクエスト中のユーザーに通知
            for passenger_id in lobby.participants: # keyでループ
                if passenger_id != driver_id:  # ドライバーは除外
                    if passenger_id in self.active_connections:
                        await self.active_connections[passenger_id].send_json({
                            "type": "lobby_closed",
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
        """距離制限内のランダムなロビーを見つける（出発地と目的地の両方を考慮）"""
        async with self.lock:
            # 参加可能なロビー（距離制限内かつオープン状態）をフィルタリング
            available_lobbies = []
            
            for lobby in self.ride_lobbies.values():
                # オープン状態で満員でないロビーのみ対象
                if lobby.status != LobbyStatus.OPEN or lobby.is_full():
                    continue
                
                # 既にリクエスト済みのロビーは除外
                if passenger_id in lobby.requests:
                    continue
                
                # 出発地の距離チェック
                start_distance = await self.calculate_distance(passenger_location, lobby.starting_location)
                
                # 目的地の距離チェック
                destination_distance = float('inf')
                if passenger_destination and lobby.destination:
                    destination_distance = await self.calculate_distance(passenger_destination, lobby.destination)
                
                # 出発地と目的地の両方が距離制限内の場合のみ追加
                if start_distance <= max_distance and (destination_distance <= max_distance or passenger_destination is None or lobby.destination is None):
                    available_lobbies.append({
                        "lobby": lobby,
                        "start_distance": start_distance,
                        "destination_distance": destination_distance if destination_distance != float('inf') else None
                    })
            
            if not available_lobbies:
                return None
            
            # 出発地の距離が近い順にソート
            available_lobbies.sort(key=lambda x: x["start_distance"])
            
            # 距離が近い上位3つのロビーからランダムに選択（分散させるため）
            top_count = min(3, len(available_lobbies))
            selected = random.choice(available_lobbies[:top_count])
            
            return {
                "lobby": selected["lobby"].to_dict(),
                "start_distance": selected["start_distance"],
                "destination_distance": selected["destination_distance"]
            }
    
    async def request_ride(self, passenger_id: int, lobby_id: str, passenger_location: tuple, passenger_destination: tuple) -> Dict[str, Any]:
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
            
            # リクエストを追加
            if not lobby.add_request(passenger_id, passenger_location, passenger_destination):
                return {"success": False, "error": "リクエストの追加に失敗しました"}
            
            
            # 乗客情報を登録
            self.user_lobbies[passenger_id] = lobby_id
            self.user_roles[passenger_id] = UserRole.PASSENGER
            
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
        """乗客が距離内のランダムなロビーに参加リクエスト（目的地の距離も考慮）"""
        # まず、距離内のランダムなロビーを見つける
        lobby_info = await self.find_random_lobby_by_distance(
            passenger_id, 
            passenger_location, 
            passenger_destination,
            max_distance
        )
        
        if not lobby_info:
            return {"success": False, "error": "距離内に利用可能なロビーが見つかりませんでした"}
        
        # 見つかったロビーにリクエスト
        lobby_id = lobby_info["lobby"]["lobby_id"]
        result = await self.request_ride(passenger_id, lobby_id, passenger_location, passenger_destination)
        
        print(f"ロビー情報: {result}")
        
        
        # 距離情報を追加
        if result["success"]:
            result["start_distance"] = lobby_info["start_distance"]
            result["destination_distance"] = lobby_info["destination_distance"]
        
        
            # ロビーが満員になった場合、WebSocketで通知
            if result["isfull"]:
                print("ロビーが満員になりました")
                lobby = self.ride_lobbies[lobby_id]
                participants = [lobby.driver_id] + list(lobby.requests.keys())
                print(f"active_connections: {self.active_connections}")
                # 全参加者に通知
                for user_id in participants:
                    if user_id in self.active_connections:
                        await self.active_connections[user_id].send_json({
                            "type": "lobby_full",
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
            if passenger_id not in lobby.requests:
                return {"success": False, "error": "リクエストが存在しません"}
            
            # 確定済みの場合はキャンセル不可
            if passenger_id in lobby.requests:
                return {"success": False, "error": "確定済みのリクエストはキャンセルできません"}
            
            # リクエストを削除
            del lobby.requests[passenger_id]
            
            # 承認リストからも削除
            if passenger_id in lobby.driver_approved:
                lobby.driver_approved.remove(passenger_id)
            if passenger_id in lobby.passenger_approved:
                lobby.passenger_approved.remove(passenger_id)
            
            # 乗客情報を削除
            if passenger_id in self.user_lobbies:
                del self.user_lobbies[passenger_id]
            if passenger_id in self.user_roles:
                del self.user_roles[passenger_id]
            
            return {"success": True, "message": "リクエストをキャンセルしました"}
    
    async def approve_ride(self, user_id: int, lobby_id: str):
        """マッチングした人を承認する"""
        async with self.lock:
        # ロビーの存在確認
            if lobby_id not in self.ride_lobbies:
                return {"success": False, "error": "ロビーが存在しません"}
            
            lobby = self.ride_lobbies[lobby_id]
            
            # 権限とステータスチェック
            if user_id not in lobby.requests:
                return {"success": False, "error": "リクエストが存在しません"}
            
            # 承認処理
            self.ride_lobbies[lobby_id].requests[user_id]["status"] = RequestStatus.CONFIRMED
            
            # 双方承認済みかどうか
            is_confirmed = lobby.get_approve_status()
            print(f"承認状況: {lobby.get_approve_status()}")
            
            if is_confirmed:
                match = await self._complete_matching(lobby)
            
            return match

    async def get_lobby_requests(self, driver_id: int, lobby_id: str) -> Dict[str, Any]:
        """ドライバーがロビーのリクエスト一覧を取得"""
        async with self.lock:
            # ロビーの存在確認
            if lobby_id not in self.ride_lobbies:
                return {"success": False, "error": "ロビーが存在しません"}
            
            lobby = self.ride_lobbies[lobby_id]
            
            # 権限チェック
            if lobby.driver_id != driver_id:
                return {"success": False, "error": "権限がありません"}
            
            # リクエスト一覧を取得
            requests = lobby.get_passenger_requests()
            
            return {
                "success": True,
                "lobby_id": lobby_id,
                "requests": requests,
                "requests": list(lobby.requests)
            }
    
    async def get_available_lobbies(self, passenger_location: Tuple[float, float], max_distance: float = 5.0) -> List[Dict[str, Any]]:
        """乗客が利用可能なロビー一覧を取得"""
        async with self.lock:
            available_lobbies = []
            
            for lobby in self.ride_lobbies.values():
                # オープン状態で満員でないロビーのみ対象
                if lobby.status != LobbyStatus.OPEN or lobby.is_full():
                    continue
                
                # 距離チェック
                distance = await self.calculate_distance(passenger_location, lobby.starting_location)
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
                "requests": lobby.get_passenger_requests()
            }
    
    async def get_lobby_users(self, lobby_id: str) -> List[int]:
        """ロビーに参加しているユーザーのIDを取得"""
        if lobby_id not in self.ride_lobbies:
            return []
        
        lobby = self.ride_lobbies[lobby_id]
        return [lobby.driver_id] + list(lobby.requests.keys()) # とりあえずドライバーと乗客のIDを返す
    
    async def _complete_matching(self, lobby: RideLobby) -> Match:
        """マッチングを完了してデータベースに保存"""
        # ロビーのステータスを更新
        print(f"マッチング完了: {lobby.lobby_id} - 参加者: {lobby.requests}")
        lobby.status = LobbyStatus.COMPLETED
        
        # 案内ルートを生成
        coordinates = [lobby.starting_location]  # ドライバー出発地
        pickups_deliveries = []

        for i, (pid, info) in enumerate(lobby.requests.items()):
            coordinates.append(info["passenger_location"])
            coordinates.append(info["passenger_destination"])
            pickups_deliveries.append((1 + i * 2, 1 + i * 2 + 1))

        coordinates.append(lobby.destination)  # ドライバーの目的地

        route_service = RouteGenerateService(
            api_key=settings.mapbox_api_key,
            coordinates=coordinates,
            pickups_deliveries=pickups_deliveries,
            start_index=0,
            end_index=len(coordinates) - 1
        )

        geojson = await route_service.get_geojson_route()

        if geojson:
            print("✔ 経路生成成功")
        else:
            print("❌ 経路生成に失敗しました")
        
        # データベースにマッチを作成
        match = Match(
            driver_id=lobby.driver_id, 
            status="Moving",
            driver_start_lat=lobby.starting_location[0],
            driver_start_lng=lobby.starting_location[1],
            driver_destination_lat=lobby.destination[0],
            driver_destination_lng=lobby.destination[1],
            route_geojson=geojson,
            )
        self.db.add(match)
        
        # 乗車者情報をデータベースに保存
        for passenger_id in lobby.requests:
            passenger = MatchPassenger(
                match_id=match.match_id,
                passenger_id=passenger_id,
                passenger_start_lat=passenger_id["passenger_location"][0],
                passenger_start_lng=passenger_id["passenger_location"][1],
                passenger_destination_lat=passenger_id["passenger_destination"][0],
                passenger_destination_lng=passenger_id["passenger_destination"][1]
                )
            self.db.add(passenger)
        
            
        # 参加者全員に通知
        match_participants = [lobby.driver_id] + list(lobby.requests)
        
        for user_id in match_participants:
            # WebSocketで通知
            if user_id in self.active_connections:
                await self.active_connections[user_id].send_json({
                    "type": "マッチングが確定しました。案内を開始します。",
                    "match_id": match.match_id,
                    "participants": match_participants
                })
            
            # ユーザー情報をクリア
            if user_id in self.user_lobbies:
                del self.user_lobbies[user_id]
            if user_id in self.user_roles:
                del self.user_roles[user_id]
        
        # ロビーを削除
        if lobby.lobby_id in self.ride_lobbies:
            del self.ride_lobbies[lobby.lobby_id]
        
        self.db.commit()
        self.db.refresh(match)
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