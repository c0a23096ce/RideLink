from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from api.models.models import Base

# MySQL接続URL
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root@db:3306/demo?charset=utf8"

# エンジン作成
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, echo=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def reset_database():
    """
    外部キー制約を無効化してデータベースをリセット
    """
    with engine.connect() as connection:
        # 外部キー制約を無効化
        connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        
        # 全テーブルを削除
        Base.metadata.drop_all(bind=connection)
        
        # テーブルを再作成
        Base.metadata.create_all(bind=connection)
        
        # 外部キー制約を有効化
        connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        
        # 変更をコミット
        connection.commit()