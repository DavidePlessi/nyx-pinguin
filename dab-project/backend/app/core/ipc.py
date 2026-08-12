import asyncio
from app.core.db import get_client
from app.core.config import settings
from pymongo.errors import CollectionInvalid
import pymongo

from datetime import datetime, timezone

IPC_COLLECTION = "ipc_messages"

async def init_ipc():
    client = get_client()
    db = client[settings.MONGO_DB_NAME]
    try:
        await db.create_collection(IPC_COLLECTION, capped=True, size=1048576) # 1MB capped
    except CollectionInvalid:
        stats = await db.command("collstats", IPC_COLLECTION)
        if not stats.get("capped"):
            await db.command({"convertToCapped": IPC_COLLECTION, "size": 1048576})

async def publish_message(channel: str, message: dict):
    client = get_client()
    db = client[settings.MONGO_DB_NAME]
    await db[IPC_COLLECTION].insert_one({"channel": channel, "data": message})

import traceback

async def listen_channel(channel: str, callback):
    try:
        print("Initializing IPC listener...")
        client = get_client()
        db = client[settings.MONGO_DB_NAME]
        collection = db[IPC_COLLECTION]
        
        # Trova l'ultimo documento inserito per sapere da dove iniziare ad ascoltare
        last_doc = await collection.find().sort([("$natural", -1)]).limit(1).to_list(1)
        
        if not last_doc:
            res = await collection.insert_one({"channel": "dummy", "data": "init"})
            last_id = res.inserted_id
        else:
            last_id = last_doc[0]["_id"]
        
        print(f"✅ Listening for new IPC messages after ID: {last_id}")
        
        while True:
            try:
                cursor = collection.find({"channel": channel, "_id": {"$gt": last_id}}, cursor_type=pymongo.CursorType.TAILABLE_AWAIT)
                async for doc in cursor:
                    last_id = doc["_id"] # Aggiorna il cursore
                    await callback(doc["data"])
            except Exception as e:
                print(f"IPC Listen Cursor Error: {e}")
                await asyncio.sleep(1)
    except Exception as e:
        print(f"CRITICAL ERROR IN IPC LISTENER: {e}")
        traceback.print_exc()
