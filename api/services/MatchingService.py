from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime, timedelta
from fastapi import WebSocket
from sqlalchemy.orm import Session
import asyncio
import time
from geopy.distance import geodesic 

from api.models.models import Match

class MatchPoolEntry:
    """メモリ内でマッチプールのエントリーを表現するクラス"""
    def __init__(self, player_id: int, skill_level: int, preferences: Dict[str, Any], location: Optional[Tuple[float, float]] = None):
        self.player_id = player_id  # プレイヤーID
        self.skill_level = skill_level  # スキルレベル
        self.preferences = preferences  # プレイヤーのマッチング条件
        self.location = location  # 位置情報（緯度, 経度）のタプル
        self.waiting_since = time.time()  # 待機開始時刻
        self.status = "waiting"  # 状態: waiting, matched

class MatchingService:
    def __init__(self, db: Session):
        self.db = db 
        self.active_connections: Dict[int, WebSocket] = {}  # プレイヤーIDとWebSocketの対応
        self.match_pool: Dict[int, MatchPoolEntry] = {}  # プレイヤーIDをキーとしたマッチプールエントリー
        self.match_pool_lock = asyncio.Lock()  # 同時アクセスを防ぐためのロック
        
    async def add_player_to_pool(self, player_id: int, skill_level: int, preferences: Dict[str, Any], location: Optional[Tuple[float, float]] = None) -> MatchPoolEntry:
        """プレイヤーをマッチングプールに追加"""
        async with self.match_pool_lock: # マッチングプールへのアクセスを排他的に行う
            # 既存のエントリーをチェック
            if player_id in self.match_pool: # プレイヤーIDがマッチングプールに存在する場合
                # 既存のエントリーを更新
                entry = self.match_pool[player_id]
                entry.skill_level = skill_level
                entry.preferences = preferences
                entry.location = location
                entry.waiting_since = time.time()
                return entry
            
            # 新しいエントリーを作成
            entry = MatchPoolEntry(player_id, skill_level, preferences, location)
            self.match_pool[player_id] = entry
            return entry
    
    async def remove_player_from_pool(self, player_id: int) -> bool:
        """プレイヤーをマッチングプールから削除"""
        async with self.match_pool_lock:
            if player_id not in self.match_pool:
                return False
            
            del self.match_pool[player_id]
            return True
    
    async def register_connection(self, player_id: int, websocket: WebSocket):
        """WebSocket接続を登録"""
        self.active_connections[player_id] = websocket # プレイヤーIDとWebSocketを紐付け、アクティブ接続リストに登録
        
    async def unregister_connection(self, player_id: int):
        """WebSocket接続を解除"""
        if player_id in self.active_connections: # プレイヤーIDがアクティブ接続に存在する場合
            del self.active_connections[player_id]
            # 接続が切れたらプールからも削除
            await self.remove_player_from_pool(player_id)
    
    async def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """2点間の距離を計算"""
        if coord1 is None or coord2 is None:
            return float('inf')  # 位置情報がない場合は無限大の距離とする
        
        return geodesic(coord1, coord2).kilometers  # coord1とcoord2の2点間の距離を計算し、キロメートル単位で返す

    async def find_match(self, max_distance: float = 10.0, min_players: int = 2, max_players: int = 10) -> Optional[List[MatchPoolEntry]]:
        """
        マッチングプールからマッチするプレイヤーを探す
        位置情報のみを考慮してマッチングを行う
        """
        async with self.match_pool_lock:
            # 待機中のプレイヤーを取得
            waiting_entries = [entry for entry in self.match_pool.values() if entry.status == "waiting"]
            
            if len(waiting_entries) < min_players:
                return None
            
            # マッチングアルゴリズム
            # 1. 最も長く待っているプレイヤーをベースに選択
            waiting_entries.sort(key=lambda entry: entry.waiting_since)
            base_player = waiting_entries[0]
            
            # 2. ベースプレイヤーと距離条件が合うプレイヤーを選択
            matched_players = [base_player]
            
            for entry in waiting_entries[1:]:
                # 距離条件のチェック（位置情報がある場合のみ）
                if base_player.location and entry.location:
                    distance = await self.calculate_distance(base_player.location, entry.location)
                    if distance > max_distance:
                        continue
                
                # 条件を満たすプレイヤーをマッチング候補に追加
                matched_players.append(entry)
                
                # 最大プレイヤー数に達したら終了
                if len(matched_players) >= max_players:
                    break
            
            # 最小人数を満たしているかチェック
            if len(matched_players) >= min_players:
                return matched_players
            
            return None
    
    async def create_match(self, matched_entries: List[MatchPoolEntry]) -> Dict[str, Any]:
        """マッチングを作成し、プレイヤーに通知する（データベースへの保存は行わない）"""
        # 一意のマッチングID生成（一時的なもの）
        temp_match_id = f"temp_{int(time.time())}_{len(matched_entries)}"
        
        # マッチングプールのエントリーのステータスを更新
        player_ids = []
        async with self.match_pool_lock:
            for entry in matched_entries: # MatchPoolEntryのリストをループ
                player_id = entry.player_id # MatchPoolEntryクラスのプレイヤーIDを取得
                player_ids.append(player_id) # プレイヤーIDをリストに追加
                if player_id in self.match_pool: # マッチングプールにプレイヤーIDが存在する場合
                    self.match_pool[player_id].status = "matched" # マッチングプールのステータスを"matched"に更新
        
        # マッチング情報を作成
        match_info = {
            "match_id": temp_match_id,
            "players": player_ids,
            "created_at": time.time(),
            "expires_at": time.time() + 90  # 30秒以内に承認が必要
        }
        
        # マッチングしたプレイヤーに通知
        for entry in matched_entries:
            player_id = entry.player_id
            if player_id in self.active_connections: # プレイヤーIDがアクティブ接続に存在する場合
                websocket = self.active_connections[player_id] # プレイヤーIDに対応するWebSocketを取得
                await websocket.send_json({ # WebSocketを利用してプレイヤーにマッチング情報を送信
                    "type": "match_found",
                    "match_id": temp_match_id,
                    "players": player_ids,
                    "expires_at": match_info["expires_at"]
                })
        
        return match_info # マッチング情報を返す
    
    """
    異なるインスタンスが建てられるため、以下の変数はクラス変数として定義
    """
    # 承認用の一時マッチング情報を保持する辞書
    temp_matches: Dict[str, Dict[str, Any]] = {}
    """
    Dict[key, match_info = {
        "match_id": temp_match_id, str型
        "players": player_ids, list型
        "created_at": time.time(),
        "expires_at": time.time() + 90  # 30秒以内に承認が必要
    }]
    """
    # プレイヤーの承認状態を保持する辞書
    match_confirmations: Dict[str, Set[int]] = {}

    async def confirm_match(self, match_id: str, player_id: int) -> Optional[Match]:
        """プレイヤーがマッチングを承認する"""
        # 一時マッチングが存在するか確認
        if match_id not in self.temp_matches:
            return None
        
        match_info = self.temp_matches[match_id] # マッチングIDに対応したmatch_infoを取得
        
        # 承認期限を確認
        if time.time() > match_info["expires_at"]:
            # 期限切れなら一時マッチングを削除し、プレイヤーをマッチングプールに戻す
            await self._cancel_temp_match(match_id)
            return None
        
        # プレイヤーがこのマッチングに含まれているか確認
        if player_id not in match_info["players"]:
            return None
        
        # プレイヤーの承認を記録 同じプレイヤーが複数回承認しても問題ないようにset型で記録
        if match_id not in self.match_confirmations:
            self.match_confirmations[match_id] = set()
        self.match_confirmations[match_id].add(player_id) # 重複しないプレイヤーIDを追加
        
        # マッチ内のすべてのプレイヤーが承認したか確認
        if len(self.match_confirmations[match_id]) == len(match_info["players"]):
            # すべてのプレイヤーが承認したらデータベースにマッチを作成
            return await self._create_confirmed_match(match_id)
        
        return None

    async def _create_confirmed_match(self, match_id: str) -> Match:
        """承認されたマッチをデータベースに作成"""
        match_info = self.temp_matches[match_id]
        
        # データベースにマッチを作成
        match = Match(status="matched")
        self.db.add(match)
        self.db.flush()  # IDを取得するためにフラッシュ
        
        # プレイヤーをマッチに割り当て
        for i, player_id in enumerate(match_info["players"]):
            # マッチングが成立したプレイヤーをプールから削除
            await self.remove_player_from_pool(player_id)
            
            # プレイヤーに最終的なマッチ成立を通知
            if player_id in self.active_connections:
                websocket = self.active_connections[player_id]
                await websocket.send_json({
                    "type": "match_confirmed",
                    "match_id": match.match_id,
                    "db_match_id": match.match_id
                })
        
        self.db.commit()
        
        # 一時マッチング情報と承認情報を削除
        del self.temp_matches[match_id]
        if match_id in self.match_confirmations:
            del self.match_confirmations[match_id]
        
        return match

    async def _cancel_temp_match(self, match_id: str):
        """一時的なマッチングをキャンセルし、プレイヤーをマッチングプールに戻す"""
        if match_id not in self.temp_matches:
            return
        
        match_info = self.temp_matches[match_id]
        
        # マッチングプールのエントリーのステータスを"waiting"に戻す
        async with self.match_pool_lock:
            for player_id in match_info["players"]:
                if player_id in self.match_pool:
                    self.match_pool[player_id].status = "waiting"
                    
                    # プレイヤーにマッチングキャンセルを通知
                    if player_id in self.active_connections:
                        websocket = self.active_connections[player_id]
                        await websocket.send_json({
                            "type": "match_cancelled",
                            "match_id": match_id,
                            "reason": "timeout"
                        })
        
        # 一時マッチング情報と承認情報を削除
        del self.temp_matches[match_id]
        if match_id in self.match_confirmations:
            del self.match_confirmations[match_id]

    async def run_matchmaking_cycle(self):
        """マッチメイキングサイクルを実行"""
        # 期限切れの一時マッチングをチェック
        current_time = time.time()
        expired_matches = []
        for match_id, match_info in self.temp_matches.items():
            if current_time > match_info["expires_at"]:
                expired_matches.append(match_id)
        
        # 期限切れのマッチングをキャンセル
        for match_id in expired_matches:
            await self._cancel_temp_match(match_id)
        
        # 新しいマッチングを探す
        matched_entries = await self.find_match()
        if matched_entries:
            match_info = await self.create_match(matched_entries)
            # 一時マッチング情報を保存
            self.temp_matches[match_info["match_id"]] = match_info
    
    # def get_pool_stats(self) -> Dict[str, Any]:
    #     """マッチングプールの統計情報を取得"""
    #     waiting_count = len([e for e in self.match_pool.values() if e.status == "waiting"])
    #     return {
    #         "total_players": len(self.match_pool),
    #         "waiting_players": waiting_count,
    #         "skill_distribution": self._get_skill_distribution()
    #     }
    
    # def _get_skill_distribution(self) -> Dict[str, int]:
    #     """スキルレベルの分布を取得"""
    #     distribution = {
    #         "low": 0,    # 1000未満
    #         "medium": 0, # 1000-1500
    #         "high": 0    # 1500以上
    #     }
        
    #     for entry in self.match_pool.values():
    #         if entry.skill_level < 1000:
    #             distribution["low"] += 1
    #         elif entry.skill_level < 1500:
    #             distribution["medium"] += 1
    #         else:
    #             distribution["high"] += 1
                
    #     return distribution
    
    # def get_queue_position(self, player_id: int) -> Optional[Dict[str, Any]]:
    #     """プレイヤーのキュー内での位置情報を取得"""
    #     if player_id not in self.match_pool:
    #         return None
            
    #     entry = self.match_pool[player_id]
    #     if entry.status != "waiting":
    #         return None
            
    #     # 待機時間
    #     waiting_time = time.time() - entry.waiting_since
        
    #     # 同じスキルレンジにあるプレイヤー数
    #     skill_range = 200  # マッチングに使用する同じスキル差
    #     similar_skill_count = 0
        
    #     for other_entry in self.match_pool.values():
    #     return {
    #         "waiting_time": waiting_time,
    #         "similar_skill_players": similar_skill_count,
    #         "estimated_wait": max(0, 30 - waiting_time) if similar_skill_count >= 2 else 60  # 簡易な推定待ち時間
    #     }