from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
    データベースをリセットします
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)