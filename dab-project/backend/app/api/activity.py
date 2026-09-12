from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from app.models.models import GuildConfig
from app.models.activity import PlayerActivity, EventTrack
from app.services.raid_helper import fetch_and_store_raid_helper_activity
import logging
from datetime import datetime, timedelta, timezone

router = APIRouter()
logger = logging.getLogger(__name__)

from app.api.oauth import get_current_user

@router.get("/{guild_id}")
async def get_activity(guild_id: str, from_date: Optional[str] = None, to_date: Optional[str] = None, user = Depends(get_current_user)) -> Dict[str, Any]:
    query = {"guild_id": guild_id}
    
    if from_date or to_date:
        query["date"] = {}
        if from_date:
            try:
                fd = datetime.fromisoformat(from_date)
                query["date"]["$gte"] = fd
            except ValueError:
                pass
        if to_date:
            try:
                td = datetime.fromisoformat(to_date)
                query["date"]["$lte"] = td
            except ValueError:
                pass
        if not query["date"]:
            del query["date"]

    activities = await PlayerActivity.find(query).to_list()
    
    # Per total_events_in_period count unique event_ids from EventTrack in the same date range
    # Wait, EventTrack has processed_at, but we need the event's date. 
    # Since PlayerActivity holds the event date, we can just find distinct event_id in activities!
    unique_events = set(act.event_id for act in activities)
    total_events_in_period = len(unique_events)
    
    player_data = {}
    weekly_data = {}
    event_data = {}
    
    for act in activities:
        pid = act.player_id
        eid = act.event_id
        
        if pid not in player_data:
            player_data[pid] = {
                "player_id": pid,
                "player_name": act.player_name,
                "total_events": 0,
                "events": []
            }
        player_data[pid]["total_events"] += 1
        player_data[pid]["events"].append({
            "event_id": eid,
            "event_name": act.event_name,
            "date": act.date.isoformat(),
            "source": act.source
        })
        
        if eid not in event_data:
            event_data[eid] = {
                "event_id": eid,
                "event_name": act.event_name,
                "date": act.date.isoformat(),
                "source": act.source,
                "participants": []
            }
        event_data[eid]["participants"].append({
            "player_id": act.player_id,
            "player_name": act.player_name
        })
        
        # Aggregate by week (e.g. 2023-W45)
        # Using ISO calendar week
        year, week, _ = act.date.isocalendar()
        week_str = f"{year}-W{week:02d}"
        if week_str not in weekly_data:
            weekly_data[week_str] = {}
        if pid not in weekly_data[week_str]:
            weekly_data[week_str][pid] = 0
        weekly_data[week_str][pid] += 1
        
    return {
        "total_events": total_events_in_period,
        "players": list(player_data.values()),
        "events": list(event_data.values()),
        "weekly_data": weekly_data
    }

from app.api.oauth import get_current_guild_admin

@router.post("/sync/{guild_id}")
async def sync_activity(guild_id: str, admin = Depends(get_current_guild_admin)):
    guild = await GuildConfig.find_one(GuildConfig.guild_id == guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")
        
    if not guild.raid_helper_api_key:
        raise HTTPException(status_code=400, detail="Raid-Helper API key not configured for this guild")
        
    await fetch_and_store_raid_helper_activity(guild)
    return {"status": "success", "message": "Activity synchronized successfully"}
