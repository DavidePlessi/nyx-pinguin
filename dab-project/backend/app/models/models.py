from beanie import Document
from typing import List, Optional
from datetime import datetime

class GuildConfig(Document):
    guild_id: str
    name: str = "Nuova Gilda"
    source_channel_id: Optional[str] = None
    source_role_id: Optional[str] = None
    member_role_id: Optional[str] = None
    dest_channels: List[str] = []
    external_dest_channels: List[str] = []
    is_active: bool = False

    class Settings:
        name = "guild_configs"

class AdminUser(Document):
    discord_id: str
    username: str
    role: str = "user"
    added_at: datetime = datetime.utcnow()

    class Settings:
        name = "admin_users"

class BotLog(Document):
    timestamp: datetime = datetime.utcnow()
    level: str = "info"
    message: str

    class Settings:
        name = "bot_logs"

class GuildMusicStatus(Document):
    guild_id: str
    active_bots: list = []
    last_updated: datetime = datetime.utcnow()

    class Settings:
        name = "guild_music_status"

class ApiInstances(Document):
    type: str = "config"
    piped: List[str] = []
    invidious: List[str] = []

    class Settings:
        name = "api_instances"
