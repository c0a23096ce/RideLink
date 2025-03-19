from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
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
    
    # 1対多のリレーション: 1人のユーザーは複数の旅行リクエストを持つ
    trip_requests = relationship("TripRequest", back_populates="user")

class TripRequest(Base):
    __tablename__ = 'trip_requests'
    
    request_id = Column(Integer, primary_key=True)  # リクエストの一意のID
    user_id = Column(Integer, ForeignKey('users.user_id'))  # どのユーザーがリクエストしたか
    current_latitude = Column(Float)    # 現在地の緯度
    current_longitude = Column(Float)   # 現在地の経度
    destination_latitude = Column(Float)  # 目的地の緯度
    destination_longitude = Column(Float) # 目的地の経度
    departure_time = Column(DateTime)   # 出発予定時刻
    status = Column(String(50))         # リクエストの状態（'active'/'matched'/'completed'/'cancelled'）
    created_at = Column(DateTime, default=func.now())  # リクエスト作成日時
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 最終更新日時
    
    # 多対1のリレーション: 各リクエストは1人のユーザーに属する
    user = relationship("User", back_populates="trip_requests")
    
    # 1対多のリレーション: 1つのリクエストは複数のマッチングで「リクエスト側」になりうる
    matches_as_requester = relationship("Match", foreign_keys="Match.request_id1")
    
    # 1対多のリレーション: 1つのリクエストは複数のマッチングで「マッチング側」になりうる
    matches_as_matched = relationship("Match", foreign_keys="Match.request_id2")

class Match(Base):
    __tablename__ = 'matches'
    
    match_id = Column(Integer, primary_key=True)  # マッチングの一意のID
    request_id1 = Column(Integer, ForeignKey('trip_requests.request_id'))  # リクエスト側のID
    request_id2 = Column(Integer, ForeignKey('trip_requests.request_id'))  # マッチング側のID
    status = Column(String(50))  # マッチングの状態（'pending'/'accepted'/'rejected'/'completed'）
    created_at = Column(DateTime, default=func.now())  # マッチング作成日時
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 最終更新日時
    
    # 多対1のリレーション: 各マッチングはリクエスト側のTripRequestに関連
    requester = relationship("TripRequest", foreign_keys=[request_id1])
    
    # 多対1のリレーション: 各マッチングはマッチング側のTripRequestに関連
    matched = relationship("TripRequest", foreign_keys=[request_id2])
    
    # 1対多のリレーション: 1つのマッチングは複数の履歴エントリーを持つ
    history = relationship("MatchHistory", back_populates="match")

class MatchHistory(Base):
    __tablename__ = 'match_history'
    
    history_id = Column(Integer, primary_key=True)  # 履歴の一意のID
    match_id = Column(Integer, ForeignKey('matches.match_id'))  # 関連するマッチングのID
    previous_status = Column(String(50))  # 状態変更前の値
    new_status = Column(String(50))       # 状態変更後の値
    changed_by = Column(Integer, ForeignKey('users.user_id'))  # 誰が変更したか
    created_at = Column(DateTime, default=func.now())  # 履歴作成日時（状態変更日時）
    
    # 多対1のリレーション: 各履歴エントリーは1つのマッチングに関連
    match = relationship("Match", back_populates="history")
    
    # 多対1のリレーション: 各履歴エントリーは状態を変更したユーザーに関連
    user = relationship("User")