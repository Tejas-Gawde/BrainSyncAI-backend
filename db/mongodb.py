from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

client = None
db = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]
    # indexes
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    await db.playgrounds.create_index([("owner", 1)])
    await db.playgrounds.create_index([("members", 1)])
    await db.subjects.create_index([("playground_id", 1)])
    # messages are stored at playground level now
    await db.messages.create_index([("playground_id", 1), ("timestamp", 1)])

def get_db():
    if db is None:
        raise RuntimeError("Database not connected. Startup event didn't run.")
    return db

async def close_db():
    global client
    if client:
        client.close()
