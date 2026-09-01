from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.models import GuildConfig, AdminUser, BotLog, GuildMusicStatus, ApiInstances, AvailableLanguage
from app.models.guild_drops import DropUser, Build, DropHistory, DropPoll, WeaponClassMapping

class Database:
    client: AsyncIOMotorClient | None = None

db_instance = Database()

async def init_db():
    db_instance.client = AsyncIOMotorClient(settings.MONGO_URI)
    database = db_instance.client[settings.MONGO_DB_NAME]
    await init_beanie(database=database, document_models=[GuildConfig, AdminUser, BotLog, GuildMusicStatus, ApiInstances, AvailableLanguage, DropUser, Build, DropHistory, DropPoll, WeaponClassMapping])
    
    # Seeding default languages
    default_langs = [
        AvailableLanguage(code="it", name="Italiano", emoji="🇮🇹"),
        AvailableLanguage(code="en", name="Inglese (UK)", emoji="🇬🇧"),
        AvailableLanguage(code="en", name="Inglese (US)", emoji="🇺🇸"),
        AvailableLanguage(code="fr", name="Francese", emoji="🇫🇷"),
        AvailableLanguage(code="es", name="Spagnolo", emoji="🇪🇸"),
        AvailableLanguage(code="el", name="Greco", emoji="🇬🇷"),
        AvailableLanguage(code="sv", name="Svedese", emoji="🇸🇪"),
        AvailableLanguage(code="sl", name="Sloveno", emoji="🇸🇮"),
        AvailableLanguage(code="de", name="Tedesco", emoji="🇩🇪"),
        AvailableLanguage(code="ru", name="Russo", emoji="🇷🇺"),
        AvailableLanguage(code="uk", name="Ucraino", emoji="🇺🇦")
    ]
    
    for lang in default_langs:
        existing = await AvailableLanguage.find_one(AvailableLanguage.emoji == lang.emoji)
        if not existing:
            await lang.insert()

async def close_db():
    if db_instance.client:
        db_instance.client.close()

def get_client() -> AsyncIOMotorClient:
    return db_instance.client
