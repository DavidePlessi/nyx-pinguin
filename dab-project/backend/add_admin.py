import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.models import AdminUser
import sys

async def main():
    if len(sys.argv) < 3:
        print("Uso: python add_admin.py <DISCORD_ID> <USERNAME> [RUOLO]")
        sys.exit(1)
    
    discord_id = sys.argv[1]
    username = sys.argv[2]
    role = sys.argv[3] if len(sys.argv) > 3 else "user"

    print("Connessione al database...")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    database = client[settings.MONGO_DB_NAME]
    await init_beanie(database=database, document_models=[AdminUser])

    existing = await AdminUser.find_one(AdminUser.discord_id == discord_id)
    if existing:
        print(f"L'utente {username} ({discord_id}) esiste già! Ruolo attuale: {existing.role}")
        existing.role = role
        await existing.save()
        print(f"Ruolo aggiornato a {role}.")
    else:
        admin = AdminUser(discord_id=discord_id, username=username, role=role)
        await admin.save()
        print(f"✅ Utente {username} ({discord_id}) aggiunto con ruolo {role}!")

if __name__ == "__main__":
    asyncio.run(main())
