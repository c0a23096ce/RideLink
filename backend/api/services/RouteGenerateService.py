from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from typing import List, Tuple, Optional
import httpx


class RouteGenerateService:
    def __init__(
        self,
        api_key: str, # MapboxのAPIキー
        coordinates: List[Tuple[float, float]], # 各地点の (latitude, longitude) のリスト
        pickups_deliveries: List[Tuple[int, int]], # 拾い上げる地点と降ろす地点のインデックスのリスト
        start_index: int, # ドライバーの開始地点のインデックス
        end_index: int # ドライバーの目的地のインデックス
    ):
        """
        :param api_key: MapboxのAPIキー
        :param coordinates: 各地点の (latitude, longitude) のリスト
        :param pickups_deliveries: [(pickup_index, dropoff_index), ...]
        :param start_index: ドライバーの開始地点のインデックス
        :param end_index: ドライバーの目的地のインデックス
        """
        self.api_key = api_key
        self.coordinates = coordinates
        self.pickups_deliveries = pickups_deliveries
        self.start_index = start_index
        self.end_index = end_index

    async def build_distance_matrix(self) -> List[List[int]]:
        """
        Mapbox Matrix APIを使用して、地点間の距離行列を作成
        """
        coord_str = ";".join([f"{lon},{lat}" for lat, lon in self.coordinates])
        url = f"https://api.mapbox.com/directions-matrix/v1/mapbox/driving/{coord_str}"
        params = {
            "access_token": self.api_key
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        print("レスポンス:", response.json())
        
        return data["durations"]

    def create_data_model(self, distance_matrix: List[List[int]]) -> dict:
        return {
            "distance_matrix": distance_matrix,
            "pickups_deliveries": self.pickups_deliveries,
            "starts": [self.start_index],
            "ends": [self.end_index]
        }

    def solve_route_order(self, distance_matrix: List[List[int]]) -> Optional[List[int]]:
        """
        OR-Tools を使って訪問順序を計算する（pickup → dropoff の制約付き）
        """
        print("訪問順序計算中...")
        data = self.create_data_model(distance_matrix)

        manager = pywrapcp.RoutingIndexManager(
            len(data["distance_matrix"]),
            1,  # 車両数 = 1
            data["starts"],
            data["ends"]
        )

        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(data["distance_matrix"][from_node][to_node])

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # ✅ ここで「time」ディメンションを追加
        routing.AddDimension(
            transit_callback_index,
            0,          # slack（余裕時間）
            100000,     # 最大走行時間（適当な大きい値）
            True,       # 最初のノードの時間を0に固定する
            "time"      # ディメンション名（CumulVarで使う）
        )
        time_dimension = routing.GetDimensionOrDie("time")

        # ✅ pickup → dropoff の順序制約
        for pickup, delivery in data["pickups_deliveries"]:
            pickup_index = manager.NodeToIndex(pickup)
            delivery_index = manager.NodeToIndex(delivery)
            routing.AddPickupAndDelivery(pickup_index, delivery_index)
            routing.solver().Add(routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))
            routing.solver().Add(
                time_dimension.CumulVar(pickup_index) <= time_dimension.CumulVar(delivery_index)
            )

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            index = routing.Start(0)
            route_order = []
            while not routing.IsEnd(index):
                route_order.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))
            route_order.append(manager.IndexToNode(index))
            print("訪問順序計算完了")
            return route_order
        else:
            return None


    async def get_geojson_route(self) -> Optional[dict]:
        """
        全体処理：
        ① 距離行列作成 → ② 最適訪問順算出 → ③ Mapbox Directions APIでルート取得
        → 最終的に GeoJSON を返す
        """
        print("経路生成中...")
        distance_matrix = await self.build_distance_matrix()
        route_order = self.solve_route_order(distance_matrix)

        if not route_order:
            return None

        ordered_coords = [self.coordinates[i] for i in route_order]
        coord_str = ";".join([f"{lon},{lat}" for lat, lon in ordered_coords])

        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coord_str}"
        params = {
            "access_token": self.api_key,
            "geometries": "geojson",
            "overview": "full"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        
        print(f'return_data: {data["routes"][0]["geometry"]}')
        return data["routes"][0]["geometry"]


