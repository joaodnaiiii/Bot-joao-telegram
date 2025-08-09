from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

Base = declarative_base()

engine = create_async_engine(settings.database_url, echo=False, future=True)

AsyncSessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession, autoflush=False, autocommit=False
)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session