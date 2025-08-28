"""
Database connection and session management.
"""

import asyncio
import logging
from typing import AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.infrastructure.config import Settings
from app.infrastructure.models import Base

logger = logging.getLogger(__name__)

# Global session factory
_session_factory = None


async def create_database_session(settings: Settings) -> async_sessionmaker[AsyncSession]:
    """Create and configure database session factory."""
    global _session_factory
    
    if _session_factory is None:
        # Create async engine
        engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        
        # Create session factory
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database session factory created successfully")
    
    return _session_factory


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    if _session_factory is None:
        raise RuntimeError("Database session factory not initialized")
    
    async with _session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def check_database_connection(settings: Settings) -> bool:
    """Check if database connection is working."""
    try:
        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
        
        await engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def wait_for_database(settings: Settings, max_retries: int = 30, delay: int = 2) -> bool:
    """Wait for database to be available."""
    logger.info("Waiting for database to be available...")
    
    for attempt in range(max_retries):
        if await check_database_connection(settings):
            logger.info("Database is available")
            return True
        
        logger.info(f"Database not available, attempt {attempt + 1}/{max_retries}")
        await asyncio.sleep(delay)
    
    logger.error("Database connection timeout")
    return False 