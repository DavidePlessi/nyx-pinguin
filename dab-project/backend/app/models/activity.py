from beanie import Document
from typing import Optional
from datetime import datetime

class PlayerActivity(Document):
    guild_id: str
    player_id: str
    player_name: str
    event_id: str
    event_name: str
    date: datetime
    source: str = "raid-helper"

    class Settings:
        name = "player_activity"

class EventTrack(Document):
    guild_id: str
    event_id: str
    processed_at: datetime

    class Settings:
        name = "event_track"
