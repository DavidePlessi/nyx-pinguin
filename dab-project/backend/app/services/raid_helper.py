import httpx
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from app.models.models import GuildConfig
from app.models.activity import PlayerActivity, EventTrack

logger = logging.getLogger(__name__)

async def fetch_and_store_raid_helper_activity(guild: GuildConfig):
    if not guild.raid_helper_api_key:
        return
        
    api_key = guild.raid_helper_api_key
    guild_id = guild.guild_id
    
    url = f"https://raid-helper.xyz/api/v4/servers/{guild_id}/events"
    headers = {
        "Authorization": api_key,
        "IncludeSignUps": "true"
    }
    if guild.raid_helper_channel_id:
        headers["ChannelFilter"] = guild.raid_helper_channel_id
        
    # We will fetch events from the last 30 days to ensure we don't miss anything 
    # StartTimeFilter takes unix timestamp in seconds
    thirty_days_ago = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp())
    headers["StartTimeFilter"] = str(thirty_days_ago)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch Raid-Helper events for guild {guild_id}: {response.text}")
                return
                
            data = response.json()
            events = data.get("postedEvents", [])
            
            for event in events:
                event_id = event.get("id")
                start_time_ts = event.get("startTime")
                
                # We only process if the event has already started
                if not start_time_ts:
                    continue
                    
                start_time = datetime.fromtimestamp(start_time_ts, tz=timezone.utc)
                if start_time > datetime.now(timezone.utc):
                    continue
                    
                # Instead of skipping processed events, we delete old records for this event
                # to support admins editing the event later (e.g. marking no-shows as Absence).
                await PlayerActivity.find(PlayerActivity.event_id == event_id, PlayerActivity.guild_id == guild_id).delete()
                    
                # Store sign-ups
                sign_ups = event.get("signUps", [])
                event_title = event.get("title", "Unknown Event")
                
                for sign_up in sign_ups:
                    player_id = sign_up.get("userId") or sign_up.get("id")
                    player_name = sign_up.get("name")
                    class_name = sign_up.get("className") or sign_up.get("class", "")
                    
                    if not player_id:
                        continue
                        
                    # Filter out non-attending roles mimicking the Raid-Helper Attendance API logic
                    excluded_roles = ["Bench", "Late", "Tentative", "Absence", "Maybe", "Declined"]
                    if class_name and any(class_name.lower() == role.lower() for role in excluded_roles):
                        continue
                        
                    activity = PlayerActivity(
                        guild_id=guild_id,
                        player_id=str(player_id),
                        player_name=player_name or "Unknown",
                        event_id=event_id,
                        event_name=event_title,
                        date=start_time,
                        source="raid-helper"
                    )
                    await activity.insert()
                    
                # Mark as processed (still useful for fast checks if we wanted, but not blocking updates now)
                track = await EventTrack.find_one(EventTrack.event_id == event_id, EventTrack.guild_id == guild_id)
                if track:
                    track.processed_at = datetime.utcnow()
                    await track.save()
                else:
                    track = EventTrack(
                        guild_id=guild_id,
                        event_id=event_id,
                        processed_at=datetime.utcnow()
                    )
                    await track.insert()
                logger.info(f"Processed event {event_id} ({event_title}) for guild {guild_id}")
                
    except Exception as e:
        logger.error(f"Exception during Raid-Helper sync for guild {guild_id}: {e}")

async def sync_all_guilds_activity():
    guilds = await GuildConfig.find(GuildConfig.raid_helper_api_key != None).to_list()
    for guild in guilds:
        await fetch_and_store_raid_helper_activity(guild)
