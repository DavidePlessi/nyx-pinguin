import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.models import GuildConfig

async def main():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    database = client[settings.MONGO_DB_NAME]
    await init_beanie(database=database, document_models=[GuildConfig])

    configs = await GuildConfig.find_all().to_list()
    for c in configs:
        print(f"Guild: {c.guild_id} - Role: {c.source_role_id}")

if __name__ == "__main__":
    asyncio.run(main())
