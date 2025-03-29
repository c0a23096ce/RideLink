from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime, timedelta
from fastapi import WebSocket
from sqlalchemy.orm import Session
import asyncio
import time
import uuid
import random
from geopy.distance import geodesic 

from api.models.models import Match, MatchPassenger

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
        
        self.lobby_id = lobby_id
        self.driver_id = driver_id
        self.starting_location = starting_location
        self.destination = destination
        self.max_distance = max_distance
        self.max_passengers = max_passengers
        self.preferences = preferences
        self.created_at = time.time()
        self.status = LobbyStatus.OPEN
        
        # 参加リクエスト管理: {passenger_id: {"status": status, "timestamp": time}}
        self.requests: Dict[int, Dict[str, Any]] = {}
        
        # 確定した乗客リスト（双方が承認したもの）
        self.confirmed_passengers: Set[int] = set()
        
        # ドライバーが承認した乗客リスト
        self.driver_approved: Set[int] = set()
        
        # 乗客が承認したリスト
        self.passenger_approved: Set[int] = set()

    def add_request(self, passenger_id: int) -> bool:
        """乗車リクエストを追加"""
        # すでに満員の場合は拒否
        if len(self.confirmed_passengers) >= self.max_passengers:
            return False
            
        # すでにリクエスト済みの場合
        if passenger_id in self.requests:
            return False
            
        # 新しいリクエストを追加
        self.requests[passenger_id] = {
            "status": RequestStatus.PENDING,
            "timestamp": time.time()
        }
        return True
    
    def driver_approve(self, passenger_id: int) -> bool:
        """ドライバーが乗客を承認"""
        # リクエストが存在しない場合は失敗
        if passenger_id not in self.requests:
            return False
        
        # ドライバー承認リストに追加
        self.driver_approved.add(passenger_id)
        
        # 片方がすでに承認している場合は確定
        if passenger_id in self.passenger_approved:
            self.confirmed_passengers.add(passenger_id)
            self.requests[passenger_id]["status"] = RequestStatus.CONFIRMED
            
        return True
    
    def passenger_approve(self, passenger_id: int) -> bool:
        """乗客が乗車を承認"""
        if passenger_id not in self.requests:
            return False
        
        # 乗客承認リストに追加
        self.passenger_approved.add(passenger_id)
        
        # 片方がすでに承認している場合は確定
        if passenger_id in self.driver_approved:
            self.confirmed_passengers.add(passenger_id)
            self.requests[passenger_id]["status"] = RequestStatus.CONFIRMED
            
        return True
        
    def is_full(self) -> bool:
        """ロビーが満員かどうか"""
        print(f"ロビー内の乗客数: {len(self.confirmed_passengers)}, 最大乗客数: {self.max_passengers}")
        return len(self.confirmed_passengers) >= self.max_passengers
        
    def to_dict(self) -> Dict[str, Any]:
        """ロビー情報を辞書に変換"""
        return {
            "lobby_id": self.lobby_id,
            "driver_id": self.driver_id,
            "starting_location": self.starting_location,
            "destination": self.destination,
            "max_distance": self.max_distance,
            "max_passengers": self.max_passengers,
            "current_passengers": len(self.confirmed_passengers),
            "status": self.status,
            "created_at": self.created_at,
            "preferences": self.preferences
        }
    
    def get_passenger_requests(self) -> Dict[int, Dict[str, Any]]:
        """全リクエスト情報を取得"""
        result = {}
        for passenger_id, request_data in self.requests.items():
            result[passenger_id] = request_data.copy()
            # 各種承認状態をTrue/Falseで追加
            result[passenger_id]["driver_approved"] = passenger_id in self.driver_approved # ドライバーが承認済みか
            result[passenger_id]["passenger_approved"] = passenger_id in self.passenger_approved # 乗客が承認済みか
            result[passenger_id]["confirmed"] = passenger_id in self.confirmed_passengers # 双方承認済みか
        return result

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
            self.ride_lobbies = {}
            self.user_lobbies = {}
            self._initialized = True
        elif db is not None:
            self.db = db  # DBオブジェクトは常に更新

        self.active_connections: Dict[int, WebSocket] = {}  # ユーザーIDとWebSocketの対応
        self.user_roles: Dict[int, str] = {}  # ユーザーID: 役割(driver/passenger)
        self.lock = asyncio.Lock()  # 排他制御用ロック
        
    async def register_connection(self, user_id: int, websocket: WebSocket):
        """WebSocket接続を登録"""
        self.active_connections[user_id] = websocket
        
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
            self.user_lobbies[driver_id] = lobby_id
            self.user_roles[driver_id] = UserRole.DRIVER
            
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
            if lobby.driver_id != driver_id:
                return {"success": False, "error": "ロビーを閉じる権限がありません"}
            
            # ロビーを閉じる
            lobby.status = LobbyStatus.CLOSED
            
            # 参加リクエスト中のユーザーに通知
            for passenger_id in lobby.requests:
                if passenger_id in self.active_connections:
                    await self.active_connections[passenger_id].send_json({
                        "type": "lobby_closed",
                        "lobby_id": lobby_id,
                        "message": "ドライバーがロビーを閉じました"
                    })
                    
                    # 乗客のロビー関連情報をクリア
                    if passenger_id in self.user_lobbies and self.user_lobbies[passenger_id] == lobby_id:
                        del self.user_lobbies[passenger_id]
                        if passenger_id in self.user_roles:
                            del self.user_roles[passenger_id]
            
            # ドライバーの情報もクリア
            del self.user_lobbies[driver_id]
            del self.user_roles[driver_id]
            
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
    
    async def request_ride(self, passenger_id: int, lobby_id: str) -> Dict[str, Any]:
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
            if not lobby.add_request(passenger_id):
                return {"success": False, "error": "リクエストの追加に失敗しました"}
            
            # 乗客情報を登録
            self.user_lobbies[passenger_id] = lobby_id
            self.user_roles[passenger_id] = UserRole.PASSENGER
            
            # ドライバーに通知
            if lobby.driver_id in self.active_connections:
                await self.active_connections[lobby.driver_id].send_json({
                    "type": "new_ride_request",
                    "lobby_id": lobby_id,
                    "passenger_id": passenger_id
                })
            
            return {
                "success": True,
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
        result = await self.request_ride(passenger_id, lobby_id)
        
        # 距離情報を追加
        if result["success"]:
            result["start_distance"] = lobby_info["start_distance"]
            result["destination_distance"] = lobby_info["destination_distance"]
        
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
            if passenger_id in lobby.confirmed_passengers:
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
            
            # ドライバーに通知
            if lobby.driver_id in self.active_connections:
                await self.active_connections[lobby.driver_id].send_json({
                    "type": "ride_request_cancelled",
                    "lobby_id": lobby_id,
                    "passenger_id": passenger_id
                })
            
            return {"success": True, "message": "リクエストをキャンセルしました"}
    
    async def driver_approve_passenger(self, driver_id: int, lobby_id: str, passenger_id: int) -> Dict[str, Any]:
        """ドライバーが乗客を承認"""
        async with self.lock:
            # ロビーの存在確認
            if lobby_id not in self.ride_lobbies:
                return {"success": False, "error": "ロビーが存在しません"}
            
            lobby = self.ride_lobbies[lobby_id]
            
            # 権限チェック
            if lobby.driver_id != driver_id:
                return {"success": False, "error": "権限がありません"}
            
            # リクエストの存在確認
            if passenger_id not in lobby.requests:
                return {"success": False, "error": "リクエストが存在しません"}
            
            # 承認処理
            if not lobby.driver_approve(passenger_id):
                return {"success": False, "error": "承認に失敗しました"}
            
            # 双方承認済みかどうか
            is_confirmed = passenger_id in lobby.confirmed_passengers
            
            # 乗客に通知
            if passenger_id in self.active_connections:
                await self.active_connections[passenger_id].send_json({
                    "type": "driver_approved",
                    "lobby_id": lobby_id,
                    "confirmed": is_confirmed,
                    "message": "ドライバーがあなたの乗車を承認しました" + 
                              ("。マッチングが確定しました。" if is_confirmed else "。あなたの承認が必要です。")
                })
            
            # マッチング成立の場合はデータベースに保存
            if is_confirmed and lobby.is_full():
                await self._complete_matching(lobby)
            
            return {
                "success": True,
                "message": "乗客を承認しました" + ("。マッチングが確定しました。" if is_confirmed else ""),
                "confirmed": RequestStatus.CONFIRMED if is_confirmed else RequestStatus.PENDING
            }
    
    async def passenger_approve_ride(self, passenger_id: int, lobby_id: str) -> Dict[str, Any]:
        """乗客が乗車を承認"""
        async with self.lock:
            # ロビーの存在確認
            if lobby_id not in self.ride_lobbies:
                return {"success": False, "error": "ロビーが存在しません"}
            
            lobby = self.ride_lobbies[lobby_id]
            
            # 権限とステータスチェック
            if passenger_id not in lobby.requests:
                return {"success": False, "error": "リクエストが存在しません"}
            
            # 承認処理
            if not lobby.passenger_approve(passenger_id):
                return {"success": False, "error": "承認に失敗しました"}
            
            # 双方承認済みかどうか
            is_confirmed = passenger_id in lobby.confirmed_passengers
            
            # ドライバーに通知
            if lobby.driver_id in self.active_connections:
                await self.active_connections[lobby.driver_id].send_json({
                    "type": "passenger_approved",
                    "lobby_id": lobby_id,
                    "passenger_id": passenger_id,
                    "confirmed": is_confirmed,
                    "message": "乗客が乗車を承認しました" + 
                              ("。マッチングが確定しました。" if is_confirmed else "。あなたの承認が必要です。")
                })
            
            # マッチング成立の場合はデータベースに保存
            if is_confirmed and lobby.is_full():
                await self._complete_matching(lobby)
            
            return {
                "success": True,
                "message": "乗車を承認しました" + ("。マッチングが確定しました。" if is_confirmed else ""),
                "confirmed": RequestStatus.CONFIRMED if is_confirmed else RequestStatus.PENDING
            }
    
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
                "confirmed_passengers": list(lobby.confirmed_passengers)
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

    
    async def _complete_matching(self, lobby: RideLobby) -> Match:
        """マッチングを完了してデータベースに保存"""
        # ロビーのステータスを更新
        print(f"マッチング完了: {lobby.lobby_id} - 参加者: {lobby.confirmed_passengers}")
        lobby.status = LobbyStatus.COMPLETED
        
        # データベースにマッチを作成
        match = Match(
            driver=lobby.driver_id, 
            status="Moving",
            )
        self.db.add(match)
        
        # 乗車者情報をデータベースに保存
        for passenger_id in lobby.confirmed_passengers:
            passenger = MatchPassenger(
                match_id=match.match_id,
                passenger_id=passenger_id
            )
            self.db.add(passenger)
            
            
        # 参加者全員に通知
        match_participants = [lobby.driver_id] + list(lobby.confirmed_passengers)
        
        for user_id in match_participants:
            # WebSocketで通知
            if user_id in self.active_connections:
                await self.active_connections[user_id].send_json({
                    "type": "match_completed",
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
            
            return {"success": True, "message": "マッチングが完了しました"}