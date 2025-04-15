from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, JSON
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
    driver_id = Column(Integer)  # ドライバーのID
    status = Column(String(50))  # 案内中のステータス（'pending'/'accepted'/'rejected'/'completed'）
    driver_start_lat = Column(Float, nullable=False)  # ドライバーの開始位置（緯度）
    driver_start_lng = Column(Float, nullable=False)  # ドライバーの開始位置（経度）
    driver_destination_lat = Column(Float, nullable=False)  # ドライバーの目的地（緯度）
    driver_destination_lng = Column(Float, nullable=False)  # ドライバーの目的地（経度）
    route_geojson = Column(JSON, nullable=True)  # 生成されたルートを保存するJSONカラム
    created_at = Column(DateTime, default=func.now())  # マッチング作成日時
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 最終更新日時

class MatchPassenger(Base):
    __tablename__ = 'match_passengers'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer)
    passenger_id = Column(Integer)
    passenger_start_lat = Column(Float, nullable=False)  # 乗車者の開始位置（緯度）
    passenger_start_lng = Column(Float, nullable=False)  # 乗車者の開始位置（経度）
    passenger_destination_lat = Column(Float, nullable=False)  # 乗車者の目的地（緯度）
    passenger_destination_lng = Column(Float, nullable=False)  # 乗車者の目的地（経度）
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())