"""Database connection and session management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from ...config.settings import settings


class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self) -> None:
        """Initialize database manager."""
        self.engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            poolclass=NullPool if "sqlite" in settings.database_url else None,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
        )
        
        self.async_session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        async with self.async_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close database connections."""
        await self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async for session in db_manager.get_session():
        yield session 