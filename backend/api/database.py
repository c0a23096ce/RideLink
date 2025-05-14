from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from models.models import Base
import asyncio

# MySQL接続URL
# この部分だけ変える
SQLALCHEMY_DATABASE_URL = "mysql+aiomysql://root@db:3306/demo?charset=utf8"

# エンジン作成
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)


async def reset_database():
    """
    データベース内のすべてのテーブルを削除してリセット
    """
    async with engine.begin() as connection:
        # 外部キー制約を無効化
        await connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        
        # データベース内のすべてのテーブルを削除
        tables = await connection.execute(text("SHOW TABLES"))
        table_names = [row[0] for row in tables]
        for table in table_names:
            await connection.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
        
        # テーブルを再作成
        await connection.run_sync(Base.metadata.create_all)
        
        # 外部キー制約を有効化
        await connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))