import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.models import AdminUser
import sys

async def main():
    if len(sys.argv) < 3:
        print("Uso: python add_admin.py <DISCORD_ID> <USERNAME>")
        sys.exit(1)
    
    discord_id = sys.argv[1]
    username = sys.argv[2]

    print("Connessione al database...")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    database = client[settings.MONGO_DB_NAME]
    await init_beanie(database=database, document_models=[AdminUser])

    existing = await AdminUser.find_one(AdminUser.discord_id == discord_id)
    if existing:
        print(f"L'utente {username} ({discord_id}) è già un amministratore!")
    else:
        admin = AdminUser(discord_id=discord_id, username=username)
        await admin.save()
        print(f"✅ Utente {username} ({discord_id}) aggiunto con successo agli amministratori!")

if __name__ == "__main__":
    asyncio.run(main())
