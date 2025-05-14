from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, func, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)  # ユーザーの一意のID
    name = Column(String(255), nullable=False)   # ユーザーの名前（長さを指定）
    email = Column(String(255), unique=True, nullable=False)  # ユーザーのメールアドレス（長さを指定）
    phone = Column(String(20), nullable=False)   # ユーザーの電話番号（長さを指定）
    hashed_password = Column(String(255), nullable=False)  # ハッシュ化されたパスワード

class Match(Base):
    __tablename__ = 'matches'
    
    match_id = Column(Integer, primary_key=True)  # マッチングの一意のID
    status = Column(String(50), nullable=False)  # 案内中のステータス（'pending'/'accepted'/'rejected'/'completed'）
    route_geojson = Column(JSON, nullable=True)  # 生成されたルートを保存するJSONカラム
    max_passengers = Column(Integer, default=1, nullable=False)  # 最大乗車人数
    max_distance = Column(DECIMAL(10, 6), default=5.0, nullable=False)  # 最大距離
    preferences = Column(JSON, nullable=True)  # ユーザーの好みを保存するJSONカラム
    created_at = Column(DateTime, default=func.now())  # マッチング作成日時
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 最終更新日時

    # リレーションを定義
    match_users = relationship("MatchUser", back_populates="match", cascade="all, delete-orphan")

class MatchUser(Base):
    __tablename__ = 'match_users'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.match_id'), nullable=False)  # 外部キーを設定
    user_id = Column(Integer, nullable=False)
    user_start_lat = Column(DECIMAL(10, 6), nullable=False)  # ユーザーの開始位置（緯度）
    user_start_lng = Column(DECIMAL(10, 6), nullable=False)  # ユーザーの開始位置（経度）
    user_destination_lat = Column(DECIMAL(10, 6), nullable=False)  # ユーザーの目的地（緯度）
    user_destination_lng = Column(DECIMAL(10, 6), nullable=False)  # ユーザーの目的地（経度）
    user_role = Column(String(50), nullable=False)  # ユーザーの役割（'driver'/'passenger'）
    user_status = Column(String(50), nullable=False)  # ユーザーのステータス（'pending'/'accepted'/'rejected'/'completed'）
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # リレーションを定義
    match = relationship("Match", back_populates="match_users")

class MatchHistory(Base):
    __tablename__ = 'match_history'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, nullable=False)  # 元のマッチID
    status = Column(String(50), nullable=False)  # ステータス
    route_geojson = Column(JSON, nullable=True)  # ルート情報
    max_passengers = Column(Integer, nullable=False)  # 最大乗車人数
    max_distance = Column(DECIMAL(10, 6), nullable=False)  # 最大距離
    preferences = Column(JSON, nullable=True)  # ユーザーの好み
    created_at = Column(DateTime, default=func.now())  # マッチ作成日時
    completed_at = Column(DateTime, default=func.now(), onupdate=func.now())  # マッチ完了日時

class MatchUsersHistory(Base):
    __tablename__ = 'match_users_history'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, nullable=False)  # 元のマッチID
    user_id = Column(Integer, nullable=False)  # ユーザーID
    user_start_lat = Column(DECIMAL(10, 6), nullable=False)  # 開始位置（緯度）
    user_start_lng = Column(DECIMAL(10, 6), nullable=False)  # 開始位置（経度）
    user_destination_lat = Column(DECIMAL(10, 6), nullable=False)  # 目的地（緯度）
    user_destination_lng = Column(DECIMAL(10, 6), nullable=False)  # 目的地（経度）
    user_role = Column(String(50), nullable=False)  # ユーザーの役割
    user_status = Column(String(50), nullable=False)  # ユーザーのステータス
    created_at = Column(DateTime, default=func.now())  # 作成日時
    completed_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 完了日時

class Evaluation(Base):
    __tablename__ = 'evaluations'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, nullable=False)  # マッチID
    evaluator_id = Column(Integer, nullable=False)  # 評価者のユーザーID
    evaluatee_id = Column(Integer, nullable=False)  # 被評価者のユーザーID
    rating = Column(Integer, nullable=True)  # 評価（1-5）
    status = Column(String(50), nullable=False)  # ステータス（'Waiting'/'Evaluated'）
    created_at = Column(DateTime, default=func.now())  # 作成日時
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 更新日時