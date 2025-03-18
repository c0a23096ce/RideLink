from geopy.distance import geodesic  # geopyライブラリからgeodesic関数をインポート

class MatchingService:
    def __init__(self, max_distance_km=5):
        # max_distance_kmは、マッチングの際に許容される最大距離（キロメートル）を設定
        self.max_distance_km = max_distance_km

    def calculate_distance(self, coord1, coord2):
        # coord1とcoord2の2点間の距離を計算し、キロメートル単位で返す
        return geodesic(coord1, coord2).kilometers

    def find_matches(self, users):
        matches = []  # マッチング結果を格納するリスト
        for i, user1 in enumerate(users):
            for j, user2 in enumerate(users):
                if i >= j:
                    # 同じユーザーや既にチェック済みのペアはスキップ
                    continue
                # ユーザー1とユーザー2の現在地間の距離を計算
                current_distance = self.calculate_distance(user1['current_location'], user2['current_location'])
                # ユーザー1とユーザー2の目的地間の距離を計算
                destination_distance = self.calculate_distance(user1['destination'], user2['destination'])
                # 現在地と目的地の両方が許容距離内であればマッチング
                if current_distance <= self.max_distance_km and destination_distance <= self.max_distance_km:
                    matches.append((user1, user2))  # マッチング結果をリストに追加
        return matches  # マッチング結果を返す