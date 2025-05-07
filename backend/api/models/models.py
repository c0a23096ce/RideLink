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
    is_deleted = Column(Boolean, default=0)  # 削除フラグ（0: 有効, 1: 削除済み）
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
    is_deleted = Column(Boolean, default=0)  # 削除フラグ（0: 有効, 1: 削除済み）
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # リレーションを定義
    match = relationship("Match", back_populates="match_users")