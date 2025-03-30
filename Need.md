サービス層（serviceフォルダ）
ビジネスロジックやデータ処理を担当する部分です。

1. ユーザーサービス（UserService）
ユーザーアカウント管理
認証・認可処理
プロフィール情報管理
ユーザー評価処理
2. 位置情報サービス（LocationService）
距離計算ロジック
ルート探索・最適化
座標変換
到着時間予測アルゴリズム
3. リクエスト管理サービス（RequestService）
リクエスト状態管理
リクエスト検索ロジック
有効期限管理
リクエスト条件マッチング
4. マッチングサービス（MatchingService）
近距離ユーザーマッチングアルゴリズム
マッチング候補抽出・生成
マッチング状態管理
ルート最適化計算
5. 通知サービス（NotificationService）
通知メッセージ生成
通知送信処理
通知優先度決定
プッシュ通知連携
6. 支払いサービス（PaymentService）
料金計算
決済処理連携
割引適用ロジック
料金分割計算
7. セキュリティサービス（SecurityService）
データ暗号化・復号化
アクセス制限確認
不正利用検知
セキュリティポリシー適用
8. 履歴管理サービス（HistoryService）
傾向分析
レポート生成
統計データ計算
履歴検索ロジック
CRUD層（crudフォルダ）
データベースとの直接的なやり取りを担当する部分です。

1. ユーザーCRUD（UserCRUD）
ユーザーレコード作成
ユーザー情報読み取り
ユーザー情報更新
ユーザー削除（または非アクティブ化）
ユーザー検索クエリ実行
2. リクエストCRUD（RequestCRUD）
旅行リクエスト作成
リクエスト情報取得
リクエスト更新
リクエスト削除
特定条件によるリクエスト検索
3. マッチングCRUD（MatchCRUD）
マッチングレコード作成
マッチング情報取得
マッチングステータス更新
マッチング削除
複数条件によるマッチング検索
4. 履歴CRUD（HistoryCRUD）
履歴レコード作成
履歴データ取得
履歴更新（必要な場合）
履歴アーカイブ処理
期間指定による履歴検索
5. 通知CRUD（NotificationCRUD）
通知レコード作成
通知情報取得
通知状態更新（既読など）
古い通知の削除/アーカイブ
ユーザー別通知一覧取得
6. 支払いCRUD（PaymentCRUD）
支払いレコード作成
支払い情報取得
支払い状態更新
支払い履歴検索
決済情報保存
7. 設定CRUD（SettingCRUD）
システム設定保存
設定値取得
設定更新
ユーザー固有設定管理
ルーター層（routerフォルダ）
HTTPリクエストの受付と応答を担当する部分です。

1. ユーザールーター（UserRouter）
POST /users（ユーザー登録）
POST /login（ログイン）
GET /users/{user_id}（プロフィール表示）
PUT /users/{user_id}（プロフィール更新）
POST /users/{user_id}/vehicles（車両情報登録）
GET /users/{user_id}/rating（評価閲覧）
POST /users/{user_id}/rating（評価投稿）
2. リクエストルーター（RequestRouter）
POST /requests（リクエスト作成）
GET /requests/{request_id}（リクエスト詳細取得）
PUT /requests/{request_id}（リクエスト更新）
DELETE /requests/{request_id}（リクエストキャンセル）
GET /users/{user_id}/requests（ユーザーのリクエスト一覧）
3. マッチングルーター（MatchingRouter）
POST /matching（マッチング実行）
GET /matches/{match_id}（マッチング詳細）
PUT /matches/{match_id}/approve（承認）
PUT /matches/{match_id}/reject（拒否）
GET /users/{user_id}/matches（ユーザーのマッチング一覧）
4. 旅行実行ルーター（TripRouter）
GET /trips/{trip_id}（旅行詳細取得）
PUT /trips/{trip_id}/status（状態更新）
PUT /trips/{trip_id}/complete（完了報告）
PUT /trips/{trip_id}/cancel（キャンセル）
POST /trips/{trip_id}/messages（メッセージ送信）
5. 通知ルーター（NotificationRouter）
GET /notifications（通知一覧取得）
PUT /notifications/{notification_id}/read（既読マーク）
PUT /users/{user_id}/notification-settings（通知設定更新）
6. 支払いルーター（PaymentRouter）
POST /payments（支払い処理）
GET /payments/{payment_id}（支払い詳細）
GET /users/{user_id}/payments（支払い履歴）
GET /payments/{payment_id}/receipt（領収書発行）
7. 管理者ルーター（AdminRouter）
GET /admin/users（ユーザー一覧管理）
GET /admin/statistics（統計情報）
PUT /admin/system-settings（システム設定管理

フロントプロジェクト構成例
/src
  /components         # 再利用可能なUI部品
    /Header.jsx
    /RideRequestForm.jsx
    /Map.jsx
  /pages              # 画面単位のコンポーネント
    /Login.jsx
    /DriverDashboard.jsx
    /PassengerDashboard.jsx
  /services           # APIとの通信
    /authService.js
    /matchingService.js
  /store              # 状態管理
  /utils              # ユーティリティ関数
  App.jsx             # ルーティング設定
  main.jsx            # エントリーポイント