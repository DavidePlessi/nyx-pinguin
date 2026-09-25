from beanie import Document
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

class DropUser(Document):
    discord_id: str
    username: str
    avatar: Optional[str] = None
    role: str = "user" # user, admin (globale)
    guilds: List[str] = [] # Lista di Guild ID a cui l'utente appartiene
    joined_at: datetime = datetime.utcnow()

    class Settings:
        name = "drop_users"

class GuildConfig(Document):
    guild_id: str
    name: str = "Nuova Gilda"
    source_channel_id: Optional[str] = None
    source_role_id: Optional[str] = None
    member_role_id: Optional[str] = None
    dest_channels: List[str] = []
    external_dest_channels: List[str] = []
    is_active: bool = False
    translation_channel: bool = True
    translation_ephemeral: bool = False
    translation_service: str = "mymemory"
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
    drop_min_weekly_activity: int = 5500
    
    # Bot UI Language
    bot_language: str = "en"
    
    # Drops UI Settings
    drop_strict_primary: bool = True

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

class BotLog(Document):
    timestamp: datetime = datetime.utcnow()
    level: str = "info"
    message: str

    class Settings:
        name = "bot_logs"

class BuildSlotItem(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None
    mainCategory: str
    subCategory: str

class BuildSlots(BaseModel):
    main_weapon: Optional[BuildSlotItem] = None
    secondary_weapon: Optional[BuildSlotItem] = None
    belt: Optional[BuildSlotItem] = None
    necklace: Optional[BuildSlotItem] = None
    bracelet: Optional[BuildSlotItem] = None
    ring_1: Optional[BuildSlotItem] = None
    ring_2: Optional[BuildSlotItem] = None
    brooch: Optional[BuildSlotItem] = None
    cloak: Optional[BuildSlotItem] = None
    legs: Optional[BuildSlotItem] = None
    hands: Optional[BuildSlotItem] = None
    feet: Optional[BuildSlotItem] = None
    head: Optional[BuildSlotItem] = None
    chest: Optional[BuildSlotItem] = None

class BuildSkillcoreItem(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None

class BuildSkillcores(BaseModel):
    weapon: Optional[BuildSkillcoreItem] = None
    armor_1: Optional[BuildSkillcoreItem] = None
    armor_2: Optional[BuildSkillcoreItem] = None

class Build(Document):
    user_id: str
    guild_id: str
    status: str = "draft" # draft, pending, primary
    slots: BuildSlots = BuildSlots()
    skillcores: BuildSkillcores = BuildSkillcores()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "guild_builds"

class SkillCore(Document):
    name: str
    effect: str
    imageUrl: Optional[str] = None
    slot: str
    weapon: Optional[str] = None
    lastUpdated: Optional[datetime] = None

    class Settings:
        name = "skill_cores"

class DropHistory(Document):
    guild_id: str
    item_id: str
    item_name: str
    user_id: str
    category: str # mainCategory dell'item per calcolare la rotation
    assigned_at: datetime = datetime.utcnow()
    assigned_by: str # ID admin
    roll_type: str = "regular"

    class Settings:
        name = "drop_history"

class DropPoll(Document):
    guild_id: str
    message_id: str
    channel_id: Optional[str] = None
    item_id: str
    item_name: str
    status: str = "open" # open, closed
    poll_type: str = "item" # item, lucent
    amount: Optional[int] = None # For lucent polls
    candidates: List[str] = [] # Lista di Discord ID
    candidate_reasons: Dict[str, str] = {} # Mappatura Discord ID -> Motivazione (Build Primaria, Litograph, Build Secondaria, o nota per lucent)
    candidate_amounts: Dict[str, int] = {} # Mappatura Discord ID -> Quantità richiesta (per lucent)
    created_at: datetime = datetime.utcnow()
    created_by: str # Discord ID admin

    class Settings:
        name = "drop_polls"
