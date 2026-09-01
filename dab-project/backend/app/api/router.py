from fastapi import APIRouter
from app.api.oauth import router as oauth_router

api_router = APIRouter()

api_router.include_router(oauth_router, prefix="/oauth", tags=["oauth"])

from app.api.admin import router as admin_router
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])

from app.api.music import router as music_router
api_router.include_router(music_router, prefix="/music", tags=["music"])

from app.api.questlog import router as questlog_router
api_router.include_router(questlog_router, prefix="/questlog", tags=["questlog"])

from app.api.drops import router as drops_router
api_router.include_router(drops_router, prefix="/drops", tags=["drops"])

from app.api.oauth import get_current_admin, get_current_guild_admin
from app.models.models import AdminUser, GuildConfig, BotLog, AvailableLanguage
from app.core.config import settings
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi import BackgroundTasks
import asyncio
import os
import httpx
from app.core.ipc import publish_message

class ConfigUpdateSchema(BaseModel):
    guild_id: str
    source_channel_id: str
    source_role_id: Optional[str] = None
    dest_channels: List[str]
    external_dest_channels: List[str] = []
    is_active: bool
    translation_channel: bool = True
    translation_ephemeral: bool = False
    translation_languages: List[str] = []

@api_router.get("/config/{guild_id}")
async def get_config(guild_id: str, admin: AdminUser = Depends(get_current_guild_admin)):
    config = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
    if not config:
        return {"guild_id": guild_id, "is_active": False, "dest_channels": [], "external_dest_channels": [], "translation_channel": True, "translation_ephemeral": False, "translation_languages": []}
    return config

@api_router.post("/config")
async def save_config(data: ConfigUpdateSchema, admin: AdminUser = Depends(get_current_guild_admin)):
    config = await GuildConfig.find_one(GuildConfig.guild_id == data.guild_id)
    if not config:
        config = GuildConfig(**data.dict())
    else:
        config.source_channel_id = data.source_channel_id
        config.source_role_id = data.source_role_id
        config.dest_channels = data.dest_channels
        config.external_dest_channels = data.external_dest_channels
        config.is_active = data.is_active
        config.translation_channel = data.translation_channel
        config.translation_ephemeral = data.translation_ephemeral
        config.translation_languages = data.translation_languages
    await config.save()
    return {"status": "success", "config": config}

@api_router.get("/languages")
async def get_languages():
    langs = await AvailableLanguage.find_all().to_list()
    return langs

class LanguageSchema(BaseModel):
    code: str
    name: str
    emoji: str

@api_router.post("/languages")
async def add_language(data: LanguageSchema, admin: AdminUser = Depends(get_current_admin)):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Solo gli admin globali possono aggiungere lingue.")
    lang = await AvailableLanguage.find_one(AvailableLanguage.code == data.code)
    if not lang:
        lang = AvailableLanguage(**data.dict())
        await lang.save()
    else:
        lang.name = data.name
        lang.emoji = data.emoji
        await lang.save()
    return lang

@api_router.delete("/languages/{code}")
async def delete_language(code: str, admin: AdminUser = Depends(get_current_admin)):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Solo gli admin globali possono rimuovere lingue.")
    lang = await AvailableLanguage.find_one(AvailableLanguage.code == code)
    if lang:
        await lang.delete()
    return {"status": "success"}

@api_router.get("/discord/guilds/{guild_id}/channels")
async def get_guild_channels(guild_id: str, admin: AdminUser = Depends(get_current_guild_admin)):
    url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    headers = {"Authorization": f"Bot {settings.DISCORD_PRIMARY_TOKEN}"}
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="Failed to fetch channels from Discord")
        channels = res.json()
        # Filter only voice channels (type 2) or stage channels (type 13)
        voice_channels = [c for c in channels if c.get("type") in [2, 13]]
        return [{"id": c["id"], "name": c["name"], "type": c["type"]} for c in voice_channels]

@api_router.get("/discord/guilds/{guild_id}/roles")
async def get_guild_roles(guild_id: str, admin: AdminUser = Depends(get_current_guild_admin)):
    url = f"https://discord.com/api/v10/guilds/{guild_id}/roles"
    headers = {"Authorization": f"Bot {settings.DISCORD_PRIMARY_TOKEN}"}
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="Failed to fetch roles from Discord")
        roles = res.json()
        return [{"id": r["id"], "name": r["name"], "color": r["color"]} for r in roles]

@api_router.get("/logs")
async def get_logs(admin: AdminUser = Depends(get_current_admin)):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Solo gli amministratori possono vedere i log.")
    logs = await BotLog.find_all().sort("-timestamp").limit(100).to_list()
    logs.reverse() # return chronological
    return [{"timestamp": log.timestamp.isoformat(), "level": log.level, "message": log.message} for log in logs]

async def restart_docker_containers():
    # Invia il comando di riavvio al bot tramite IPC
    await publish_message("dab_updates", {"action": "system_restart"})
    # Attende 1.5 secondi per permettere alla risposta HTTP di arrivare al client e all'IPC di essere elaborato
    await asyncio.sleep(1.5)
    # Killa l'API. Docker (con restart: always) si occuperà di riavviarlo
    os._exit(0)

@api_router.post("/system/restart")
async def restart_system(background_tasks: BackgroundTasks, admin: AdminUser = Depends(get_current_admin)):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Solo gli amministratori possono riavviare il sistema.")
    background_tasks.add_task(restart_docker_containers)
    return {"status": "success", "message": "Restarting bot and api..."}
