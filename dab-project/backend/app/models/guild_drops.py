from beanie import Document
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

class GuildInfo(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None

class DropUser(Document):
    discord_id: str
    username: str
    avatar: Optional[str] = None
    role: str = "user" # user, admin (globale)
    guilds: List[str] = [] # Lista di Guild ID a cui l'utente appartiene
    guilds_info: List[GuildInfo] = [] # Dettagli sulle gilde
    joined_at: datetime = datetime.utcnow()

    class Settings:
        name = "drop_users"

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

class Build(Document):
    user_id: str
    guild_id: str
    character_name: Optional[str] = None
    character_class: Optional[str] = None
    play_style: Optional[str] = None
    questlog_url: Optional[str] = None
    status: str = "draft" # draft, pending, primary
    slots: BuildSlots = BuildSlots()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "guild_builds"

class WeaponClassMapping(Document):
    class_name: str
    weapon_1: str
    weapon_2: str

    class Settings:
        name = "weapon_classes"

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
    candidates: List[str] = [] # Lista di Discord ID
    created_at: datetime = datetime.utcnow()
    created_by: str # Discord ID admin

    class Settings:
        name = "drop_polls"
