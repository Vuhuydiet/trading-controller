try:
    import motor.motor_asyncio as aiomotor  # type: ignore[import-not-found]
except ImportError:
    aiomotor = None  # type: ignore[assignment]

import logging
from typing import Any, Optional

from app.shared.core.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager"""

    _instance: Optional["MongoDB"] = None
    _client: Optional[Any] = None
    _db: Optional[Any] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def connect(cls):  # type: ignore[no-untyped-def]
        """Connect to MongoDB"""
        try:
            cls._client = aiomotor.AsyncIOMotorClient(settings.MONGODB_URI)  # type: ignore[attr-defined]
            cls._db = cls._client[settings.MONGODB_DB_NAME]  # type: ignore[index,attr-defined]
            # Verify connection
            await cls._db.command("ping")  # type: ignore[union-attr]
            logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB"""
        if cls._client:
            cls._client.close()
            logger.info("Disconnected from MongoDB")

    @classmethod
    def get_db(cls) -> Any:  # type: ignore[return]
        """Get database instance"""
        if cls._db is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return cls._db


async def get_mongodb() -> Any:  # type: ignore[return]
    """Dependency injection for MongoDB"""
    return MongoDB.get_db()
