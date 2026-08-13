from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.models import GuildConfig, AdminUser, BotLog, GuildMusicStatus, ApiInstances

class Database:
    client: AsyncIOMotorClient | None = None

db_instance = Database()

async def init_db():
    db_instance.client = AsyncIOMotorClient(settings.MONGO_URI)
    database = db_instance.client[settings.MONGO_DB_NAME]
    await init_beanie(database=database, document_models=[GuildConfig, AdminUser, BotLog, GuildMusicStatus, ApiInstances])

async def close_db():
    if db_instance.client:
        db_instance.client.close()

def get_client() -> AsyncIOMotorClient:
    return db_instance.client
