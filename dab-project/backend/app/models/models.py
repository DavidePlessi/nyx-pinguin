from beanie import Document
from typing import List, Optional
from datetime import datetime

class GuildConfig(Document):
    guild_id: str
    name: str = "Nuova Gilda"
    source_channel_id: Optional[str] = None
    source_role_id: Optional[str] = None
    member_role_id: Optional[str] = None
    drop_channel_id: Optional[str] = None
    dest_channels: List[str] = []
    external_dest_channels: List[str] = []
    is_active: bool = False
    translation_channel: bool = True
    translation_ephemeral: bool = False
    translation_service: str = "mymemory" # "mymemory", "deepl", "gemini"
    translation_languages: List[str] = ["it", "en"]
    raid_helper_api_key: Optional[str] = None
    raid_helper_channel_id: Optional[str] = None
    
    # Weekly Activity Settings
    weekly_activity_enabled: bool = False
    weekly_activity_channel_id: Optional[str] = None
    weekly_activity_day: int = 3 # 0=Monday, 3=Thursday
    weekly_activity_announce_time: str = "15:00"
    weekly_activity_reminder_time: str = "21:00"
    
    # Drop Eligibility Thresholds
    drop_min_events: int = 2
    drop_strict_primary: bool = True
    drop_min_weekly_activity: int = 5500
    
    # Bot UI Language
    bot_language: str = "en"

    class Settings:
        name = "guild_configs"

class WeeklyGameActivity(Document):
    guild_id: str
    player_id: str
    player_name: str
    week_id: str # format: "YYYY-WXX" e.g., "2026-W37"
    activity_score: int
    reported_at: datetime = datetime.utcnow()
    
    class Settings:
        name = "weekly_game_activity"

class AvailableLanguage(Document):
    code: str
    name: str
    emoji: str
    
    class Settings:
        name = "available_languages"

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
