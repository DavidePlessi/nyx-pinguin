from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.api.oauth import get_current_admin
from app.models.models import AdminUser, GuildMusicStatus
from app.core.ipc import publish_message
from datetime import datetime

router = APIRouter()

class MusicCommandSchema(BaseModel):
    guild_id: str
    action: str  # play, skip, previous, pause, resume, stop
    query: Optional[str] = None
    voice_channel_id: Optional[str] = None
    bot_id: Optional[str] = None # For targeted commands

@router.get("/status/{guild_id}")
async def get_music_status(guild_id: str, admin: AdminUser = Depends(get_current_admin)):
    status = await GuildMusicStatus.find_one(GuildMusicStatus.guild_id == guild_id)
    if not status:
        return {"guild_id": guild_id, "active_bots": [], "last_updated": datetime.utcnow()}
    return status

@router.post("/command")
async def send_music_command(data: MusicCommandSchema, admin: AdminUser = Depends(get_current_admin)):
    await publish_message("dab_updates", {
        "action": f"music_{data.action}",
        "guild_id": data.guild_id,
        "query": data.query,
        "voice_channel_id": data.voice_channel_id,
        "bot_id": data.bot_id
    })
    return {"status": "success", "message": f"Comando {data.action} inviato."}
