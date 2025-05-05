class UserRole:
    """ユーザーの役割を定義する定数"""
    DRIVER = "driver"
    PASSENGER = "passenger"

class UserStatus:
    """ユーザーのステータスを定義する定数"""
    IDOL = "idol"          # 何もしていない
    SEARCHING = "searching"  # 検索中
    IN_LOBBY = "in_lobby"    # ロビーに参加中
    APPROVED = "approved"    # 自分が承認済み
    MATCHED = "matched"      # マッチング確定
    NAVIGATING = "navigating"  # ナビゲーション中
    COMPLETED = "completed"  # マッチング完了

class LobbyStatus:
    """ロビーのステータス（バックエンド/フロントエンドの連携用）"""
    OPEN = "open"                 # 参加者募集中（誰も入ってないか、承認してない）
    WAITING_APPROVAL = "waiting"  # 参加者が承認待ち（未確定）
    MATCHED = "matched"           # 全員が承認済み（マッチ確定前の待機）
    NAVIGATING = "navigating"     # 案内中（マッチ確定後、移動中）
    COMPLETED = "completed"       # 案内完了
    CLOSED = "closed"             # ドライバーがロビーを閉じた（キャンセル扱い）