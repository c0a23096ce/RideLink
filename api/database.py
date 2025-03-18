from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# MySQL接続URL
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://username:password@localhost/rideshare"

# エンジン作成
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)

# セッションファクトリ作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルのベースクラス
Base = declarative_base()