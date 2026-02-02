"""
mongodb.py - MongoDB connection using Motor (async) + Beanie ODM

Beanie is an async MongoDB ODM built on top of Motor and Pydantic.
It provides a clean, Pythonic way to interact with MongoDB.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional
import os

# Will be populated on startup
client: Optional[AsyncIOMotorClient] = None
database = None


async def connect_to_mongodb():
    """
    Connect to MongoDB Atlas or local MongoDB.
    Call this on app startup.
    """
    global client, database
    
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "scamshield")
    
    print(f"[DB] Connecting to MongoDB...")
    
    client = AsyncIOMotorClient(mongodb_url)
    database = client[db_name]
    
    # Import all document models
    from app.db.models.user import User
    from app.db.models.user_settings import UserSettings
    from app.db.models.subscription import Subscription, Plan
    from app.db.models.scan import ScanRequest
    from app.db.models.threat import BlockedThreat
    from app.db.models.session import HoneypotSession
    from app.db.models.scammer import ScammerFingerprint
    from app.db.models.token_blacklist import TokenBlacklist
    from app.db.models.api_key import APIKey
    
    # Initialize Beanie with all document models
    await init_beanie(
        database=database,
        document_models=[
            User,
            UserSettings,
            Subscription,
            Plan,
            ScanRequest,
            BlockedThreat,
            HoneypotSession,
            ScammerFingerprint,
            TokenBlacklist,
            APIKey,
        ]
    )
    
    print(f"[DB] Connected to MongoDB: {db_name}")


async def close_mongodb_connection():
    """
    Close MongoDB connection.
    Call this on app shutdown.
    """
    global client
    
    if client:
        client.close()
        print("[DB] MongoDB connection closed")


async def get_database():
    """
    Dependency to get database instance.
    """
    return database


# Health check
async def check_mongodb_health() -> bool:
    """
    Check if MongoDB is responsive.
    """
    try:
        if client:
            await client.admin.command('ping')
            return True
        return False
    except Exception:
        return False
