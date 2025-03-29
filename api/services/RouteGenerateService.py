import requests
from typing import Dict, List, Tuple, Any, Optional

class RouteGenerateService:
    """
    経路生成サービスクラス
    ドライバーと乗客の位置情報に基づいて最適な経路を計算する
    """
    
    def __init__(self, db=None, config=None):
        """
        RouteGenerateServiceの初期化
        
        Args:
            db: データベース接続（必要な場合）
            config: 設定情報（APIキーなどを含む辞書）
        """
        self.db = db
        self.config = config or {}
        self.osrm_base_url = self.config.get(
            "osrm_url", 
            "http://router.project-osrm.org/route/v1/driving"
        )
        self.avg_speed_kmh = self.config.get("avg_speed_kmh", 40)  # デフォルトの平均速度: 40km/h
    
    def route_generate(
        self,
        driver_location: Tuple[float, float],
        passenger_location: Tuple[float, float], 
        driver_destination: Tuple[float, float],
        passenger_destination: Tuple[float, float]
    ) -> Dict[str, Any]:
        """
        ドライバーと乗車者の位置情報および目的地を元に最適なルートを生成する
        
        Args:
            driver_location: ドライバーの現在位置 (緯度, 経度)
            passenger_location: 乗車者の現在位置 (緯度, 経度)
            driver_destination: ドライバーの目的地 (緯度, 経度)
            passenger_destination: 乗車者の目的地 (緯度, 経度)
            
        Returns:
            ルート情報を含む辞書
        """
        # 1. ドライバーから乗車者までのルート取得
        pickup_route = self.get_route(driver_location, passenger_location)
        
        # 2. 乗車後のルート計画
        # 2-1. パターン1: 乗車者の目的地を先に訪問
        route_option1 = self.get_route(passenger_location, passenger_destination) # 乗車者の目的地までのルート
        route_option1_part2 = self.get_route(passenger_destination, driver_destination) # ドライバーの目的地までのルート
        total_distance1 = pickup_route["distance"] + route_option1["distance"] + route_option1_part2["distance"]
        total_duration1 = pickup_route["duration"] + route_option1["duration"] + route_option1_part2["duration"]
        
        # 乗車者の目的地を先に訪問するルート
        complete_route = {
            "segments": [
                {
                    "type": "to_passenger",
                    "route": pickup_route, # ドライバーから乗車者までのルート
                    "start": driver_location,
                    "end": passenger_location
                },
                {
                    "type": "to_passenger_destination",
                    "route": route_option1, # 乗車者の目的地までのルート
                    "start": passenger_location,
                    "end": passenger_destination
                },
                {
                    "type": "to_driver_destination",
                    "route": route_option1_part2, # 乗車者の目的地からドライバーの目的地までのルート
                    "start": passenger_destination,
                    "end": driver_destination
                }
            ],
            "total_distance": total_distance1,
            "total_duration": total_duration1,
            "route_order": ["passenger_pickup", "passenger_destination", "driver_destination"]
        }
        
        return complete_route

    def get_route(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> Dict[str, Any]:
        """
        2つの位置座標の間の経路情報を取得する（OSRM使用）
        
        Args:
            origin: 出発地点の座標 (緯度, 経度)
            destination: 目的地の座標 (緯度, 経度)
            
        Returns:
            経路情報を含む辞書
        """
        try:
            # OSRM APIにリクエスト
            url = f"{self.osrm_base_url}/{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
            params = {
                "overview": "full",
                "geometries": "geojson"
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # APIのレスポンスをチェック
            if data["code"] != "Ok":
                print(f"OSRM API Error: {data['code']}")
                return self.generate_mock_route_data(origin, destination)
            
            # レスポンスからルート情報を抽出
            route = data["routes"][0]
            leg = route["legs"][0]
            
            return {
                "distance": leg["distance"],  # メートル単位
                "duration": leg["duration"],  # 秒単位
                "geometry": route["geometry"],
                "waypoints": [
                    {"location": [origin[1], origin[0]], "name": "Start"},
                    {"location": [destination[1], destination[0]], "name": "End"}
                ]
            }
            
        except Exception as e:
            print(f"OSRM APIリクエスト中にエラーが発生しました: {e}")
            return self.generate_mock_route_data(origin, destination)

    def generate_mock_route_data(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> Dict[str, Any]:
        """APIが使用できない場合にモックデータを生成"""
        return {
            "distance": self.calculate_mock_distance(origin, destination),  # メートル単位
            "duration": self.calculate_mock_duration(origin, destination),  # 秒単位
            "geometry": {
                "coordinates": [[origin[1], origin[0]], [destination[1], destination[0]]],
                "type": "LineString"
            },
            "waypoints": []
        }

    def calculate_mock_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """簡易的な距離計算（実際の実装ではより正確な方法を使用してください）"""
        import math
        lat1, lon1 = point1
        lat2, lon2 = point2
        # 簡易的な直線距離計算
        return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111000  # 緯度経度1度あたり約111kmとして概算

    def calculate_mock_duration(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """簡易的な所要時間計算（距離から推定、平均速度設定に基づく）"""
        distance = self.calculate_mock_distance(point1, point2)
        avg_speed_mps = self.avg_speed_kmh * 1000 / 3600  # km/hをm/sに変換
        return distance / avg_speed_mps  # 秒単位
