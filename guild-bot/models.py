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
    status: str = "draft" # draft, pending, primary
    slots: BuildSlots = BuildSlots()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "guild_builds"

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
