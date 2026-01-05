from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .core.config import settings

# 非同期エンジン作成
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug,
)

# セッションファクトリ
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ベースモデル
Base = declarative_base()


async def get_db() -> AsyncSession:
    """データベースセッションを取得"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
