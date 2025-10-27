from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

client: AsyncIOMotorClient = None
db = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    # ensure indexes
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)

def get_db():
    if db is None:
        raise RuntimeError("❌ Database not connected yet. Make sure startup event ran.")
    return db