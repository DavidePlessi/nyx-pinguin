from beanie import Document
from typing import List, Optional
from datetime import datetime

class GuildConfig(Document):
    guild_id: str
    source_channel_id: Optional[str] = None
    source_role_id: Optional[str] = None
    dest_channels: List[str] = []
    external_dest_channels: List[str] = []
    is_active: bool = False

    class Settings:
        name = "guild_configs"

class AdminUser(Document):
    discord_id: str
    username: str
    added_at: datetime = datetime.utcnow()

    class Settings:
        name = "admin_users"

class BotLog(Document):
    timestamp: datetime = datetime.utcnow()
    level: str = "info"
    message: str

    class Settings:
        name = "bot_logs"
