import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['discord_dab']
    docs = await db['guild_configs'].find({'guild_id': '1529123644842705018'}).to_list(None)
    for d in docs:
        print(d)

if __name__ == "__main__":
    asyncio.run(main())
