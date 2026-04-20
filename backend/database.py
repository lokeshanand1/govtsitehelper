"""
GovScheme Advisor — MongoDB Database Connection & Helpers
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "govscheme_advisor")

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Connect to MongoDB."""
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # Create indexes
    await db.schemes.create_index("scheme_id", unique=True)
    await db.schemes.create_index("category")
    await db.schemes.create_index("state")
    await db.schemes.create_index([("name", "text"), ("description", "text"), ("eligibility_text", "text")])
    await db.users.create_index("email", unique=True)
    
    print(f"  ✅ Connected to MongoDB: {DATABASE_NAME}")
    return db


async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("  ✅ MongoDB connection closed")


def get_db():
    """Get database instance."""
    return db
