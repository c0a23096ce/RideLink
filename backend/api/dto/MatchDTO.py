from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class MatchDTO:
    match_id: int  # マッチングの一意のID
    status: str  # 案内中のステータス（'pending'/'accepted'/'rejected'/'completed'）
    route_geojson: Optional[Dict[str, Any]]  # 生成されたルートを保存するJSON
    max_passengers: int  # 最大乗車人数
    max_distance: float  # 最大距離
    preferences: Optional[Dict[str, Any]]  # ユーザーの好みを保存するJSON
    created_at: str  # マッチング作成日時（ISOフォーマットなど）
    updated_at: str  # 最終更新日時（ISOフォーマットなど）

@dataclass
class MatchUserDTO:
    id: int  # ユーザーの一意のID
    match_id: int  # マッチID（外部キー）
    user_id: int  # ユーザーID
    user_start_lat: float  # ユーザーの開始位置（緯度）
    user_start_lng: float  # ユーザーの開始位置（経度）
    user_destination_lat: float  # ユーザーの目的地（緯度）
    user_destination_lng: float  # ユーザーの目的地（経度）
    user_role: str  # ユーザーの役割（'driver'/'passenger'）
    user_status: str  # ユーザーのステータス（'pending'/'accepted'/'rejected'/'completed'）
    created_at: str  # 作成日時（ISOフォーマットなど）
    updated_at: str  # 更新日時（ISOフォーマットなど）